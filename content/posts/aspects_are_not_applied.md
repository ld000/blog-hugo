---
title: '翻译: Spring AOP 讨论最多的问题 #1 - aspects 没有生效'
date: 2017-06-12
tags: ["aspect", "spring", "java"]
---

> 原文：http://denis-zhdanov.blogspot.com/2009/07/spring-aop-top-problem-1-aspects-are.html

这篇文章继续讨论从 [Spring AOP top problem #2 - java.lang.ClassCastException: $Proxy7](http://denis-zhdanov.blogspot.com/2009/05/spring-aop-top-problem-2.html) 开始的话题。在这个话题里，我想要说明一些现在接触 spring AOP 的 spring 用户(特别是新用户)讨论最多(从我的观点看来)的问题。

<!--more-->

现在我想要聊一聊自身调用('self-calls')，如果你有这方面的经验可以跳过接下来的内容.

请注意 spring 文档也描述了一个同样的问题 - [8.6.1 Understanding AOP proxies](http://docs.spring.io/spring/docs/3.0.x/spring-framework-reference/html/ch08s06.html#aop-understanding-aop-proxies)。然而，我发现通过 spring 论坛里的很多文章显示人们并没有发现这个问题。所以，我想要把这个问题解释的更明白些 / 用我的语言。

让我们创建一个说明这个问题的例子。假设我们是 spring 的新用户而且用 spring aop 写了一个非常酷的代码，并且运行的很好。

`AopService.java`
```java
package com.spring.aop;

import org.springframework.stereotype.Component;

@Component
public class AopService {

    public void service() {
        System.out.println("AopService.service()");
    }

    public void anotherService() {
        System.out.println("AopService.anotherService()");
    }
}
```

`TestAspect.java`
```java
package com.spring.aop;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Around;
import org.springframework.stereotype.Component;

@Component
@Aspect
public class TestAspect {

    @Around("execution(* com.spring.aop.AopService.*(..))")
    public Object advice(ProceedingJoinPoint joinPoint) throws Throwable {
        System.out.println("TestAspect.advice()");
        return joinPoint.proceed();
    }
}

```

`spring-config.xml`
```xml

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:aop="http://www.springframework.org/schema/aop"
       xmlns:context="http://www.springframework.org/schema/context"
       xsi:schemaLocation="
  http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-2.5.xsd
  http://www.springframework.org/schema/aop http://www.springframework.org/schema/aop/spring-aop-2.5.xsd
  http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context-2.5.xsd">

    <context:component-scan base-package="com.spring.aop"/>
    <aop:aspectj-autoproxy/>

</beans>
```

`SpringStart.java`
```java
package com.spring;

import com.spring.aop.AopService;
import org.springframework.context.support.ClassPathXmlApplicationContext;

public class SpringStart {
    public static void main(String[] args) throws Exception {
        ClassPathXmlApplicationContext context = new ClassPathXmlApplicationContext("spring-config.xml");
        AopService service = context.getBeansOfType(AopService.class).values().iterator().next();
        service.service();
        service.anotherService();
    }
}
```

我们创建了一个包含简单的只会打印一些输出来说明被调用过的方法和简单的 aspect 注入这个类中所有 public 方法并且打印信息来说明注入被执行了的 service 类。如果我们执行 `SpringStart` 类，我们会看到期望的输出 - 方法都被注入成功。

```
TestAspect.advice()
AopService.service()
TestAspect.advice()
AopService.anotherService()
```

让我们稍微拓展下 service 类。

`AopService.java`
```java
package com.spring.aop;

import org.springframework.stereotype.Component;

@Component
public class AopService {

    public void service() {
        System.out.println("AopService.service()");
    }

    public void anotherService() {
        System.out.println("AopService.anotherService(). Calling AopService.service()...");
        service();
    }
}
```

我们期望 aspect 执行 3次 - `service()` 和 `anotherService()` 在 `SpringStart.main()` 中调用，`service()` 在 `AopService.anotherService()` 中调用。然而，如果我们运行这个例子我们发现 aspect 只执行了两次（从 `SpringStart.main()` 开始执行）i.e. `AopService.anotherService()` 中调用的 `service()` 没有被注入。

```
TestAspect.advice()
AopService.service()
TestAspect.advice()
AopService.anotherService(). Calling AopService.service()...
AopService.service()
```

通常，problem root is tightly connected to [The Law of Leaky Abstractions](https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/)。I.e. 我们对 aspect 的表现有特别的期待但是没有发现 spring aop 的规则不允许这些期待实现。

通常的解释是 spring AOP 是基于代理(proxy-based)的，i.e. 他假定当 bean 作为依赖被使用，他的方法应该用 aspect 代理包裹(be advised by particular aspect(s) the container injects aspect-aware bean proxy)而不是 bean 本身。例如，返回的代理使用和和下面代码近似的方法:

```java
public class AopServiceProxy {

    // Assuming that corresponding setters are introduced and the fields are defined.
    private TestAspect aspect;
    private AopService rawService;

    public void service() {
        aspect.advice();
        rawService.service();
    }

    public void anotherService() {
        aspect.advice();
        anotherService();
    }
}
```

I.e. 这个代理被 aspect 包裹而且在调用 `raw` bean 前他调用了必要的 aspect 方法。然而，上一个 `AopService` 实现在 `anotherService()` 内调用了 `service()` - 这样代理无法注入因为这样调用违反了 'this' 原则, i.e. 这个方法是 'rawBean' 自己调用的。这就是为什么 aspect 在这种情况下不起作用的答案。

现在，当我们明白了问题原因我们来聊聊怎么解决它。至少有三种方法：

- **aspect 建议重写代码来避免 self-calls** - 非常不方便，特别是如果你在维护遗留代码;

- **用 aspect-aware proxy 替换 self-calls, i.e. 在 anotherService() 里用 ((AopService) AopContext.currentProxy()).service() 代替 service()** - 也不方便，需要额外设置代理而且和 spring 的代码重复;

- **用 aspectj weaving** - 这是我喜欢的方案。他会直接注入 aspect 到对应的 class 里， i.e. 不需要所有的方法都必须被代理;

我会写一篇文章来说明在 spring 中怎么使用各种类型的 aspectj weaving，这样会更加清楚的说明这个问题。
