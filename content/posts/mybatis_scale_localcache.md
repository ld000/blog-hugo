---
title: MyBatis 一级缓存在分布式下的坑
date: 2019-11-24
tags: ["java"]
---

最近生产环境的余额系统在扣减余额时经常出现余额够但是提示余额不足无法扣减的情况。查看代码逻辑，发现会先查询一次判断余额是否够，再实际扣减，之后查看日志发现并没有执行查询语句就返回错误了，推测可能是 MyBatis 一级缓存没有关闭引起的脏数据问题。关闭一级缓存后果然恢复正常了。

所以有了这篇文章，验证下 MyBatis 一级缓存的生效条件。

## 一级缓存

MyBatis 默认会开启一级缓存，在同一次会话中，如果执行多次查询条件相同的 SQL，会进行优化，优先命中一级缓存，避免多次查询数据库。

这样在单机环境下是没有问题的，可以减少于数据库的交互。但是生成环境一般都是多机部署，这样一级缓存开启的情况下就容易出现脏数据。

接下来做两个实验验证下。

### 测试1

```java
public void test1() {
    SqlSession sqlSession = sqlSessionFactory.openSession(true);
    UserWalletMapperExt mapper = sqlSession.getMapper(UserWalletMapperExt.class);

    System.out.println(mapper.queryUserBalance(10L, 1));
    System.out.println(mapper.queryUserBalance(10L, 1));
    System.out.println(mapper.queryUserBalance(10L, 1));
    mapper.addBalanceByType(10L, 1, 100L);
    System.out.println(mapper.queryUserBalance(10L, 1));
    System.out.println(mapper.queryUserBalance(10L, 1));
}
```

```shell
...queryUserBalance:debug:181 ==>  Preparing: select balance from user_wallet WHERE user_id = ? and type = ? 
...queryUserBalance:debug:181 ==> Parameters: 10(Long), 1(Integer)
...queryUserBalance:debug:181 <==      Total: 1
200
200
200
...addBalanceByType:debug:181 ==>  Preparing: update user_wallet set balance = balance + ? where user_id = ? and type = ? 
...addBalanceByType:debug:181 ==> Parameters: 100(Long), 10(Long), 1(Integer)
...addBalanceByType:debug:181 <==    Updates: 1
...queryUserBalance:debug:181 ==>  Preparing: select balance from user_wallet WHERE user_id = ? and type = ? 
...queryUserBalance:debug:181 ==> Parameters: 10(Long), 1(Integer)
...queryUserBalance:debug:181 <==      Total: 1
300
300
```

可以看到在同一个session中，相同的查询在调用更新前只会执行一次。

### 测试2

```java
public void test2() {
    SqlSession sqlSession1 = sqlSessionFactory.openSession(true);
    UserWalletMapperExt mapper1 = sqlSession1.getMapper(UserWalletMapperExt.class);
    System.out.println("session1: " + mapper1.queryUserBalance(10L, 1));

    SqlSession sqlSession2 = sqlSessionFactory.openSession(true);
    UserWalletMapperExt mapper2 = sqlSession2.getMapper(UserWalletMapperExt.class);
    System.out.println("session2: " + mapper2.queryUserBalance(10L, 1));
    mapper2.addBalanceByType(10L, 1, 100L);
    System.out.println("session2: " + mapper2.queryUserBalance(10L, 1));

    System.out.println("session1: " + mapper1.queryUserBalance(10L, 1));
}
```

```shell
...queryUserBalance:debug:181 ==>  Preparing: select balance from user_wallet WHERE user_id = ? and type = ? 
...queryUserBalance:debug:181 ==> Parameters: 10(Long), 1(Integer)
...queryUserBalance:debug:181 <==      Total: 1
session1: 500
...queryUserBalance:debug:181 ==>  Preparing: select balance from user_wallet WHERE user_id = ? and type = ? 
...queryUserBalance:debug:181 ==> Parameters: 10(Long), 1(Integer)
...queryUserBalance:debug:181 <==      Total: 1
session2: 500
...addBalanceByType:debug:181 ==>  Preparing: update user_wallet set balance = balance + ? where user_id = ? and type = ? 
...addBalanceByType:debug:181 ==> Parameters: 100(Long), 10(Long), 1(Integer)
...addBalanceByType:debug:181 <==    Updates: 1
...queryUserBalance:debug:181 ==>  Preparing: select balance from user_wallet WHERE user_id = ? and type = ? 
...queryUserBalance:debug:181 ==> Parameters: 10(Long), 1(Integer)
...queryUserBalance:debug:181 <==      Total: 1
session2: 600
session1: 500
```

可以看到在 session2 更新了值得情况下，session1 依旧使用了一级缓存查询出旧值。

### 关闭一级缓存

接下来关闭一级缓存试一下，设置 LocalCache 级别为 statement 或者在语句上设置flushCache="true" 都可以。

```java
// 设置全局一级缓存级别为 STATEMENT
org.apache.ibatis.session.Configuration configuration = new org.apache.ibatis.session.Configuration();
configuration.setLocalCacheScope(LocalCacheScope.STATEMENT);
sqlSessionFactoryBean.setConfiguration(configuration);
```

```xml
<!-- 设置单个语句不使用一级缓存 -->
<select id="queryUserBalance" resultType="java.lang.Long" flushCache="true">
```

测试
```java
public void test3() {
    SqlSession sqlSession = sqlSessionFactory.openSession(true);
    UserWalletMapperExt mapper = sqlSession.getMapper(UserWalletMapperExt.class);

    System.out.println(mapper.queryUserBalance(10L, 1));
    System.out.println(mapper.queryUserBalance(10L, 1));
    System.out.println(mapper.queryUserBalance(10L, 1));
}
```

```shell
...queryUserBalance:debug:181 ==>  Preparing: select balance from user_wallet WHERE user_id = ? and type = ? 
...queryUserBalance:debug:181 ==> Parameters: 10(Long), 1(Integer)
...queryUserBalance:debug:181 <==      Total: 1
600
...queryUserBalance:debug:181 ==>  Preparing: select balance from user_wallet WHERE user_id = ? and type = ? 
...queryUserBalance:debug:181 ==> Parameters: 10(Long), 1(Integer)
...queryUserBalance:debug:181 <==      Total: 1
600
...queryUserBalance:debug:181 ==>  Preparing: select balance from user_wallet WHERE user_id = ? and type = ? 
...queryUserBalance:debug:181 ==> Parameters: 10(Long), 1(Integer)
...queryUserBalance:debug:181 <==      Total: 1
600
```

可以看到关闭一级缓存后所有语句都会实际执行。

## 总结

MyBatis 的一级缓存在单机环境下可以减少与 MySql 的交互，提高性能，但是在分布式环境下容易产生脏数据。建议在生产环境下关闭，使用 Redis，Memcache 等代替。