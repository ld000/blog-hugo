---
title: java 调用 c# 的方法
date: 2017-06-28
tags: ["java"]
---

java 调用 c# 程序的几种方式。

<!--more-->

# Native Java

Java不能直接调用C#的dll，这是因为C#和Java一样，也是运行在虚拟机上的语言，所生成的dll并不是和C++一样的native dll，因此没有办法使用JNI进行直接调用。

Java调用C#的基本思路是：

Java <=== JNI ===> C++ Native dll <=== CLR ===> C# dll

给C# dll做一个C++的wrapper，Java与C++之间通过JNI实现调用，而C++和C#之间通过CLR实现调用。

**这样做有个缺陷就是不能在 linux 上运行。**

有以下几种方法实现：

## jni4net

github: https://github.com/jni4net/jni4net

```java
import java.io.File;
import java.io.IOException;
import testlib.Test;
import net.sf.jni4net.Bridge;
...
        try {

            Bridge.setVerbose(true);
            Bridge.init();

            Bridge.LoadAndRegisterAssemblyFrom(new File("testlib.j4n.dll"));

        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }

        Test test = new Test();
        test.Hello();
        test.Repeat("It works!");
```

缺点：

1. 很长时间没更新了
2. 不支持在 Mono 和 Linux 上运行。原文：[It's not supported at the moment, sorry](http://zamboch.blogspot.cz/2010/04/jni4net-not-yet-on-mono-linux.html)
3. 性能一般

## javonet

按年收费

```java
public void GenerateRandomNumber() throws JavonetException {
    NObject objRandom = Javonet.New("System.Random");
    int value = objRandom.invoke("Next",10,20);

    System.out.println(value);
}
```

## 自己实现一个C++ native dll作为你的C# dll的代理

基本的实现思路是：

1. 对应你的C# dll，写一套Java版本的API。
2. 使用javah命令，将Java API翻译成对应的C++ API，并输出到对应的xxxxJNI.h文件中。
3. 创建C++ dll工程，添加xxxxJNI.h以及jdk提供的jni.h和jni_md.h，并启用clr支持。
4. 在C++ dll工程中通过managed C++调用你的C#dll，进而实现所有的C++ API。

操作过程可参考  [How-to-wrap-a-Csharp-library-for-use-in-Java](https://www.codeproject.com/Articles/378826/How-to-wrap-a-Csharp-library-for-use-in-Java) 和 [Java 调用 C# DLL](http://www.iteye.com/topic/1133867).

# 使用中间文件做交互

可以把输入和输出存到一个中间文本文件中(json, csv, txt)，让 c# 程序调用，然后输出一个文本文件。

缺点：

1. 过程繁琐。
2. java 和 c# 方都无法感知对方处理进度，无法方便的确定输入输出完成时间。(可以在文本结尾放置一段特殊字符作为处理结束标志)
3. 程序异常不好发现。

# 接口调用

c# 将输入封装成 http 或 socket 接口，供 java 调用。c# 程序编译成 exe，在安装了 Mono 的 Linux 机器上运行，或运行在 Mono Docker 镜像中。

---

参考

> http://ju.outofmemory.cn/entry/153844
