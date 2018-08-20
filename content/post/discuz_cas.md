---
title: discuz 接入 cas
date: 2018-07-23
tags: ["discuz", "cas"]
---

discuz 接入 cas 实现 SSO 的方法。

<!--more-->

## 版本
* Discuz 3.3
* Cas 5.x 

## 下载 casPHP 插件
`http://developer.jasig.org/cas-clients/php/`

我这里用的 1.3.0，下载完后解压拷贝到 discuz 根目录，重命名为 `CAS`。

## 去除登录输入
修改 `template/default/member/login_simple.htm`

* 删除8-29行代码，删除31-32行代码

* 添加以下代码，支持访问时 force 登录.

```sh
# 需要 CAS 打开允许 iframe, 否则报错: Refused to display 'URL' in a frame because it set 'X-Frame-Options' to 'DENY'
# cas 配置：cas.httpWebRequest.header.xframe=false
<script type="text/javascript">
(function () {
       var _body = document.body || document.getElementsByTagName('body')[0];
       var iframe = document.createElement('iframe');
       iframe.id = 'logcheck';

       iframe.src = "member.php?"+(("mod=logging&action=loginCheck"));
       iframe.style.display = 'none';
       _body.appendChild(iframe);
   })();
</script>

# TODO 现只能在 CAS 登录后才能登录，需做修改
```

## 去除弹框登录
管理中心 -> 界面 -> 去掉浮动窗口（登录）

![image](/images/discuz-cas-1.png)

## 在`CAS`文件夹中创建 `CasClientConfig.php`
```php
<?php
define ( 'CAS_SERVER_HOSTNAME', 'cas.com' );
define ( 'CAS_SERVER_PORT', 8080 ); 
define ( 'CAS_SERVER_APP_NAME', "cas" ); 
?>
```

## 在`CAS`文件夹中创建 `CasClient.php`
```php
<?php
require_once DISCUZ_ROOT.'./CAS/CasClientConfig.php'; // 注意
require_once DISCUZ_ROOT.'./CAS/CAS.php'; // 注意
                                                  
// 初始化
//phpCAS::setDebug ();
 
// initialize phpCAS
phpCAS::client ( CAS_VERSION_2_0, CAS_SERVER_HOSTNAME, CAS_SERVER_PORT, CAS_SERVER_APP_NAME );
 
// no SSL validation for the CAS server
phpCAS::setNoCasServerValidation ();

phpCAS::setNoClearTicketsFromUrl ();
phpCAS::handleLogoutRequests();

?>
```

## source/class/class_core.php第16行加入
```php
require_once DISCUZ_ROOT."CAS/CasClient.php";
```

## uc_client/control/user.php
134行注释
```php
// elseif($user['password'] != md5($passwordmd5.$user['salt'])) {
// $status = -2;
// } elseif($checkques && $user['secques'] != $_ENV['user']->quescrypt($questionid, $answer)) {
// $status = -3;
// }
```

注释 `onsynlogin`, `onsynlogout`, `onregister`方法

## source/function/function_member.php 加入
```php
// 新加的方法，用以支持CAS 登录
function userloginCas($username, $ip = '') {
    $return = array ();
    
    if(!function_exists('uc_user_login')) {
        loaducenter();
    }

    $return['ucresult'] = uc_user_login(addslashes($username), '', 0, 0,'', '', $ip);

    $tmp = array ();
    $duplicate = '';
    list ( $tmp ['uid'], $tmp ['username'], $tmp ['password'], $tmp ['email'], $duplicate ) = $return ['ucresult'];
    $return ['ucresult'] = $tmp;
    if ($duplicate && $return ['ucresult'] ['uid'] > 0 || $return ['ucresult'] ['uid'] <= 0) {
        $return ['status'] = 0;
        return $return;
    }
    
    $member = getuserbyuid ( $return ['ucresult'] ['uid'], 1 );
    if (! $member || empty ( $member ['uid'] )) {
        $return ['status'] = - 1;
        return $return;
    }
    $return ['member'] = $member;
    $return ['status'] = 1;
    if ($member ['_inarchive']) {
        C::t ( 'common_member_archive' )->move_to_master ( $member ['uid'] );
    }
    if ($member ['email'] != $return ['ucresult'] ['email']) {
        C::t ( 'common_member' )->update ( $return ['ucresult'] ['uid'], array (
                'email' => $return ['ucresult'] ['email'] 
        ) );
    }
    
    return $return;
}
```

## source/class/class_member.php
51行注释并改为
```php
// if(!submitcheck('loginsubmit', 1, $seccodestatus)) {
if (1 == 2) {
```

92行 `$_G['username'] = $_G['member']['username'] = $_G['member']['password'] = ''` 后加入
```php
phpCAS::setNoClearTicketsFromUrl ();
// 这里会检测服务器端的退出的通知，就能实现php和其他语言平台间同步登出了  
phpCAS::handleLogoutRequests();  
$username='';
if(phpCAS::isAuthenticated()){  
    $username = phpCAS::getUser ();
} else {
    $service =  $_SERVER['HTTP_REFERER'];
    phpCAS::setServerLoginUrl(phpCAS::getServerLoginURL().urlencode("?service=".$service));

    phpCAS::forceAuthentication ();
}
// if(!$_GET['password'] || $_GET['password'] != addslashes($_GET['password'])) {
// showmessage('profile_passwd_illegal');
// }
// $result = userlogin($_GET['username'], $_GET['password'], $_GET['questionid'], $_GET['answer'], $this->setting['autoidselect'] ? 'auto' : $_GET['loginfield'], $_G['clientip']);
$result = userloginCas($username, $_G['clientip']);
```

347行 `on_logout` 方法
```php
if(defined('IN_MOBILE')) {
    showmessage('location_logout_succeed_mobile', dreferer(), array('formhash' => FORMHASH, 'referer' => rawurlencode(dreferer())));
} else {
    $service =  $_SERVER['HTTP_REFERER'];
    phpCAS::logoutWithRedirectService ( $service );
// showmessage('logout_succeed', dreferer(), array('formhash' => FORMHASH, 'ucsynlogout' => $ucsynlogout, 'referer' => rawurlencode(dreferer())));
}
```

386行 `on_register`方法中
```php
if(strpos($url_forward, $this->setting['regname']) !== false) {
    $url_forward = 'forum.php';
}
// 修改掉防止当登录成功时无限跳转
$url_forward = 'forum.php';
```

`logging_ctl`类中 添加异步登录验证方法

```php
function on_loginCheck(){
    global $_G;
    $username='';
    if(phpCAS::isAuthenticated()){
        $username = phpCAS::getUser ();
    } else {
        phpCAS::setServerLoginUrl(phpCAS::getServerLoginURL());
        phpCAS::forceAuthentication ();
    }
    $result = userloginCas($username, $_G['clientip']);

    if($data = uc_get_user($username)) {
        list($uid, $username, $email) = $data;      //根据用户名获取uid进行登录
    } else {
        dexit();
    }

    if($uid > 0) {
        $member = getuserbyuid($uid, 1);            //根据uid获取用户表pre_common_member中的所有字段

        $_G['uid'] = intval($uid);
        $_G['username'] = $username;
        $_G['adminid'] = $member['adminid'];
        $_G['groupid'] = $member['groupid'];
        $_G['formhash'] = formhash();
        $_G['session']['invisible'] = getuserprofile('invisible');
        $_G['member'] = $member;
        loadcache('usergroup_'.$_G['groupid']);
        C::app()->session->isnew = true;
        C::app()->session->updatesession();

        dsetcookie('auth', authcode("{$member['password']}\t{$member['uid']}", 'ENCODE'), $cookietime, 1, true);        //这里的passwod是pre_common_member表中经过加密后的密码
        dsetcookie('loginuser',$username);
        dsetcookie('activationauth');
        dsetcookie('pmnum');

        dexit('<script type="text/javascript">window.top.location.reload();</script>');
    } else {
        dexit();
    }
}
```

## source/module/member/member_logging.php 添加允许 `loginCheck` 方法通过
第15行改为 `if(!in_array($_GET['action'], array('login', 'logout','loginCheck'))) `

## 额外配置，可选
### 自动https/http 
 `CAS/CAS/Client.php`

299行
`$this->_server['base_url'] = 'https://' . $this->_getServerHostname();`
改为
`$this->_server['base_url'] = ($this->_isHttps() ? 'https':'http').'://'. $this->_getServerHostname();`

### 关闭gateway
`CAS/CAS/Client.php`
    
1164行 
`$this->redirectToCas(true/* gateway */);`
改为
`$this->redirectToCas(false/* gateway */);`

