---
title: gorm调用sharding-proxy, 参数带单引号sql报错
date: 2020-03-27
tags: ["go", "gorm", "sharding-proxy", "MySQL"]
---

## 软件版本

sharding-proxy-3.1.0

MySQL-5.7

## 正文

最近公司某系统用 go 重构，ORM框架使用 gorm，用上了分库分表，使用 sharding-proxy 作代理。

但是上了 sharding-proxy 之后之前参数中带 `'` 的 sql 全都报错了。

```shell
// 报错信息
Error 3054: Unknown exception: Illegal input, unterminated '''.
```

```go
// 执行 sql 的代码
// 这里参数 dd'dd 中有个 '
db.Exec("update md_user_info set nickname = ? where user_id = ?", "dd'dd", 1000002082)
```

怀疑可能是没用占位符，直接拼接sql引发的问题。但是看代码又没发现啥问题，只能 debug 看下。

中间都没发现问题，直接一路 debug 到最底层 sql 库。

```go
// go/src/database/sql/sql.go

func (db *DB) execDC(ctx context.Context, dc *driverConn, release func(error), query string, args []interface{}) (res Result, err error) {
    /* ... */
    if ok {
        var nvdargs []driver.NamedValue
        var resi driver.Result
        withLock(dc, func() {
            /* ... */
            // 这里执行 statmente
            resi, err = ctxDriverExec(ctx, execerCtx, execer, query, nvdargs)
        })
        /* ... */
    }

    var si driver.Stmt
    withLock(dc, func() {
        // 这里执行 preparedStatmente
        si, err = ctxDriverPrepare(ctx, dc.ci, query)
    })
    /* ... */
}
```

debug 进 `ctxDriverExec` 方法，走到最后的 mysql 驱动。

```go
// github.com/go-sql-driver/mysql/connection.go

func (mc *mysqlConn) Exec(query string, args []driver.Value) (driver.Result, error) {
    /* ... */
        // 判断 InterpolateParams 参数，如果为 true，就注入参数执行 statmente
        // 如果为 false，就跳出回 sql.go 执行 preparedStatmente
        if !mc.cfg.InterpolateParams {
            return nil, driver.ErrSkip
        }
        // 注入参数
        // try to interpolate the parameters to save extra roundtrips for preparing and closing a statement
        prepared, err := mc.interpolateParams(query, args)
    /* ... */

    // 执行 statmente
    err := mc.exec(query)
    /* ... */
}

// 将参数注入 sql
func (mc *mysqlConn) interpolateParams(query string, args []driver.Value) (string, error) {
    /* ... */
        case string:
            buf = append(buf, '\'')
            // 这里用位与和位左移状态位来判断状态
            if mc.status&statusNoBackslashEscapes == 0 {
                buf = escapeStringBackslash(buf, v)
            } else {
                buf = escapeStringQuotes(buf, v)
            }
            buf = append(buf, '\'')
    /* ... */
}
```

这里有两个相关参数：

一个是 `statusNoBackslashEscapes`，对应 sql_mode `NO_BACKSLASH_ESCAPES`，表示将反斜杠当作普通字符，而不是转义字符。开启后生成的sql为`update md_user_info set nickname = 'dd''dd' where user_id = 1000002082`，会把单引号替换成两个单引号(这样单引号会成对，不破坏结构)。

一个是 `InterpolateParams`，对应连接参数`interpolateParams`，判断是否开启客户端 prepare，进行参数转义拼接，开启可以省掉一次和服务端的prepare交互。

debug 往下走发现参数`InterpolateParams`是`true`，发出的sql是`update md_user_info set nickname = 'dd\'dd' where user_id = 1000002082`，没有问题，然后执行 statement 报错了。

先返回程序创建数据库连接的地方。

```go
connString = fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?charset=utf8mb4&parseTime=True&loc=Local&interpolateParams=true",
        conf.User, conf.Password, conf.Host, conf.Port, conf.Database)
```

果然，参数里拼上了 `&interpolateParams=true`，去掉这个参数试下，发出的 prepare sql 是`update md_user_info set nickname = ? where user_id = ?`，执行正常。看来是 sharding-proxy 不支持客户端预编译，接收 sql 时把反斜杠丢掉了，或者没有处理转义符。

## sql 解析

先简单介绍下 sql 解析的处理过程。sql 解析分为，词法分析、语法和语义分析、优化、执行代码生成。词法分析主要是把输入转化成一个个 token，语法分析是生成语法树的过程。

```shell
            前端                      中部                后端
           /   \                      |                   |
     词法分析   语法分析                优化             执行代码生成
```

以 `update table set name = a` 为例。

词法分析生成6个 token：

![https://raw.githubusercontent.com/ld000/git-resources/master/img/20200327162605.png](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200327162605.png)

语法分析语法树：

![https://raw.githubusercontent.com/ld000/git-resources/master/img/20200327163231.png](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200327163231.png)

## sql 解析器分析

同样的 sql `update md_user_info set nickname = 'dd'dd' where user_id = 1000002082`，MySQL 正常执行，sharding-proxy 却报错，接下来分析下两者的 sql 解析器都是怎么处理这条 sql 的。

这里主要分析下词法分析转化成 token 阶段，sharding-proxy 也是在这个阶段报错的。

正常解析这条 sql 应该生成10个 token：

```shell
update
md_user_info
set
nickname
=
dd'dd
where
user_id
=
1000002082
```

### sharding-proxy

首先看下接收到的 sql 是什么，debug 进 `SQLParsingEngine` 

![https://raw.githubusercontent.com/ld000/git-resources/master/img/20200326175137.jpg](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200326175137.jpg)

可以看到接收的 sql 没有问题，接下来看 sql 解析。

update 语句解析在 `AbstractUpdateParser.parse()` 处，经过 `LexerEngine`，最后用 `Tokenizer` 生成 token。

```java
// src/main/java/io/shardingsphere/core/parsing/lexer/analyzer/Tokenizer.java

private Token scanChars(final char terminatedChar) {
    // 获取 token 的字符串长度
    int length = getLengthUntilTerminatedChar(terminatedChar);
    // 截取字符串，返回新 token
    return new Token(Literals.CHARS, input.substring(offset + 1, offset + length - 1), offset + length);
}
```

```java
// src/main/java/io/shardingsphere/core/parsing/lexer/analyzer/Tokenizer.java

// 获取 token 的字符串长度
private int getLengthUntilTerminatedChar(final char terminatedChar) {
    int length = 1;
    // 当前字符是否是检测字符
    while (terminatedChar != charAt(offset + length) 
        // 判断是否是两个相同字符
                    || hasEscapeChar(terminatedChar, offset + length)) {
        if (offset + length >= input.length()) {
            throw new UnterminatedCharException(terminatedChar);
        }
        // 处理是否是两个相同字符
        if (hasEscapeChar(terminatedChar, offset + length)) {
            length++;
        }
        length++;
    }
    return length + 1;
}
```

看下 `dd'dd` 的处理过程，这时 `terminatedChar` 的值是 `'` ，剩余要处理的字符串是 `'dd\'dd' where user_id = 1000002082` ，逐个字符向后检测。

![https://raw.githubusercontent.com/ld000/git-resources/master/img/20200327155726.png](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200327155726.png)

这里`'` 会成对解析，如果碰上`'` 没有成对的情况，就会报错。不处理转义字符。

### MySQL

再看下 MySQL 的解析器。

![https://raw.githubusercontent.com/ld000/git-resources/master/img/20200327143436.png](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200327143436.png)

看到接收的 sql 和 sharding-proxy 是一样的(多一个反斜杠是因为这里按字符串显示，多一个转义符)

转化 token 的代码在 sql_lex.cc 的 MYSQLlex → lex_one_token 方法中。

```c
// sql/sql_lex.cc

int MYSQLlex(YYSTYPE *yylval, YYLTYPE *yylloc, THD *thd)
{
    /* ... */

    token= lex_one_token(yylval, thd);

    /* ... */
}
```

普通字符的解析最后会走进 `get_text` 方法进行截取。

```c
// sql/sql_lex.cc

static char *get_text(Lex_input_stream *lip, int pre_skip, int post_skip)
{
    /* ... */

    // 处理转义字符
    if (c == '\\' &&
        !(lip->m_thd->variables.sql_mode & MODE_NO_BACKSLASH_ESCAPES))
    {                    // Escaped character
        found_escape=1;
        if (lip->eof())
    return 0;
        lip->yySkip();
    }

    /* ... */
}
```

这里有个处理转义字符的逻辑，如果当前字符是反斜杠，就向后跳两个字符，跳过转义字符。

![https://raw.githubusercontent.com/ld000/git-resources/master/img/20200327160823.png](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200327160823.png)

最终的 token 列表。(token 是个 int，对应关系在 sql_yacc.h 中)

```shell
865 UPDATE_SYM      update 
484 IDENT_QUOTED    md_user_info 
757 SET             set 
484 IDENT_QUOTED    nickname 
415 EQ              = 
828 TEXT_STRING     dd'dd
891 WHERE           where 
484 IDENT_QUOTED    user_id 
415 EQ              = 
629 NUM             1000002082
411 END_OF_INPUT
```

可以看到 sharding-proxy 因为没有处理开启客户端预编译的情况，解析报错了。

## sharding-proxy 修改

修改也很简单，加上处理转义字符的逻辑就可以了，修改 `Tokenizer` 的 `getLengthUntilTerminatedChar` 方法，增加处理转义字符的逻辑。

```java
// src/main/java/io/shardingsphere/core/parsing/lexer/analyzer/Tokenizer.java

private int getLengthUntilTerminatedChar(final char terminatedChar) {
    int length = 1;
    while (terminatedChar != charAt(offset + length) || hasEscapeChar(terminatedChar, offset + length)
    ) {
        if (offset + length >= input.length()) {
            throw new UnterminatedCharException(terminatedChar);
        }

        // 增加处理转义字符
        if ('\\' == charAt(offset + length)) {
            length++;
        } else if (hasEscapeChar(terminatedChar, offset + length)) {
            length++;
        }
        length++;
    }
    return length + 1;
}
```

这里忽略了sql_mode=NO_BACKSLASH_ESCAPES 的情况，因为 sharding-jdbc 里没有传递相关参数，包括客户端预编译的相关参数也没传递。

## 其他

在没修改的情况下顺手用 Java 也测试下 sharding-jdbc 是否支持客户端预编译。

```java
Class.forName("com.mysql.jdbc.Driver");
String url = "jdbc:mysql://localhost:3307/xxx?useServerPrepStmts=false";
String username = "xxx";
String password = "xxx";
Connection conn = DriverManager.getConnection(url, username, password);
PreparedStatement st = null;
String sql = "update md_user_info set nickname = ? where user_id = ?";

st = conn.prepareStatement(sql);
st.setString(1, "dd'dd");
st.setLong(2, 1000002082);
System.out.println(st.execute());
```

Java 库的客户端预编译参数是`useServerPrepStmts`，默认值就是 false，表示关闭服务端预编译，开启客户端预编译，为了方便看我就写上了。执行一下，果然报错了。

```shell
Exception in thread "main" java.sql.SQLException: Unknown exception: Illegal input, unterminated '''.
```
