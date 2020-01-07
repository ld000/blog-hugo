---
title: 用外置 Tomcat 部署 Spring Boot 应用
date: 2019-10-25
tags: ["java"]
---

现在越来越多的人使用 Spring Boot 来开发自己的应用了，Spring Boot 用起来是各种方便，还内置 web 容器，只需要`java -jar`就能启动应用。但有时候有些公司的 Tomcat 是单独部署，有专人维护的，这时我们就需要将 Spring Boot 应用打包成 war 部署。

## 打包方式设置为 war

修改 pom.xml 文件，将打包方式设置为 war

```xml
    <packaging>war</packaging>
```

添加 war 插件

```xml
    <plugin> 
        <groupId>org.apache.maven.plugins</groupId> 
        <artifactId>maven-war-plugin</artifactId> 
        <version>3.0.0</version> 
    </plugin>
```

将 `spring-boot-starter-web` 的 Tomcat 依赖设为 provided，这样还能继续在 IDE 里调试，而且打包时排除了 tomcat 依赖。

```xml
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <exclusions>
            <exclusion>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-tomcat</artifactId>
            </exclusion>
        </exclusions>
    </dependency>
    
    <dependency> 
    	<groupId>org.springframework.boot</groupId> 
    	<artifactId>spring-boot-starter-tomcat</artifactId> 
    	<scope>provided</scope> 
    </dependency>
```

这样 pom 文件就修改好了。

## 修改入口方法

继承`SpringBootServletInitializer`类，并且重写`configure`方法 

```java
    @SpringBootApplication 
    public class Application extends SpringBootServletInitializer { 
    
        @Override 
        protected SpringApplicationBuilder configure(SpringApplicationBuilder application) { 
            return application.sources(Application.class); 
        } 
    
        public static void main(String[] args) { 
            SpringApplication.run(Application.class, args); 
        } 
    
    }
```

这样就修改好了

## 测试

`mvn clean package` 打包后放入 tomcat webapps 文件夹里测试下

![](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200107113901.png)

顺利启动

## 启动后运行

直接用 Spring Boot 内置容器启动应用时，一些启动后运行的代码可以直接写在 main 方法里

```java
    @SpringBootApplication 
    public class Application { 
    
        public static void main(String[] args) { 
            SpringApplication.run(Application.class, args); 
    
            // 启动后运行的代码
            .....
        } 
    
    }
```

换成 war 包运行后这样写就无法运行了，因为启动不是走得 main 方法。这时可以实现 `CommandLineRunner` 接口来实现。

```java
    /**
     * Interface used to indicate that a bean should <em>run</em> when it is contained within
     * a {@link SpringApplication}. Multiple {@link CommandLineRunner} beans can be defined
     * within the same application context and can be ordered using the {@link Ordered}
     * interface or {@link Order @Order} annotation.
     * <p>
     * If you need access to {@link ApplicationArguments} instead of the raw String array
     * consider using {@link ApplicationRunner}.
     *
     * 用来指定 {@link SpringApplication} 中需要运行的 bean。可以包含多个 {@link CommandLineRunner}
     * 顺序用 {@link Ordered} 接口或 {@link Order @Order} 注解指定
     *
     * @author Dave Syer
     * @see ApplicationRunner
     */
    @FunctionalInterface
    public interface CommandLineRunner {
    
    	/**
    	 * Callback used to run the bean.
    	 * @param args incoming main method arguments
    	 * @throws Exception on error
    	 */
    	void run(String... args) throws Exception;
    
    }
```

实现这个接口后把要运行的代码写在 `run` 方法中就可以了

```java
    @Component
    @Order(value = 1)
    public class MotanSwitcherRunner implements CommandLineRunner {
        @Override
        public void run(String... args) {
            // 启动后运行的代码
            .....
        }
    }
```