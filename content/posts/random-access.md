---
title: RandomAccess 接口使用
date: 2016-03-19
tags: ["java"]
---

List 实现所使用的标记接口，用来表明其支持快速（通常是固定时间）随机访问。此接口的主要目的是允许一般的算法更改其行为，从而在将其应用到随机或连续访问列表时能提供良好的性能。

<!--more-->

##用法

Random Access List(随机访问列表)如 `ArrayList` 要实现此接口，Sequence Access List(顺序访问列表)如 `LinkedList` 不要实现。
因为两者的高效遍历算法不同

通常做法，遍历前先判断：

```java
if (list instance of RandomAccess) {       
  for(int m = 0; m < list.size(); m++){}   
}else{       
  Iterator iter = list.iterator();       
  while(iter.hasNext()){}   
}
```

随机访问列表使用循环遍历，顺序访问列表使用迭代器遍历。

##JDK 定义

`List` 实现使用的标记接口，用来表明支持快速(通常是固定时间)随机访问。这个接口的主要目的是允许一般的算法更改它们的行为，从而在随机或连续访问列表时提供更好的性能。

将操作随机访问列表(比如 `ArrayList`)的最好的算法应用到顺序访问列表(比如 `LinkedList`)时，会产生二次项行为。鼓励一般的列表算法检查给定的列表是否 `instanceof` 这个接口，防止在顺序访问列表时使用较差的算法，如果需要保证可接受的性能时可以更改算法。

公认的是随机和顺序访问的区别通常是模糊的。例如，当一些 `List` 实现很大时会提供渐进的线性访问时间，但实际是固定的访问时间。这样的 `List` 实现通常应该实现此接口。通常来说，一个 `List` 的实现类应该实现这个接口如果

```java
for (int i=0, n=list.size(); i < n; i++)
        list.get(i);
```

比

```java
 for (Iterator i=list.iterator(); i.hasNext(); )
          i.next();
```

快

##验证事例

```java
package com.ld.practice.arraylist;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.RandomAccess;

/**
 * 测试Random Access List(随机访问列表)如 ArrayList 和 Sequence Access List(顺序访问列表)如 LinkedList </br>
 * 不同遍历算法的效率</br>
 * 结论：前者用循环，后者用迭代器
 */
@SuppressWarnings({"rawtypes", "unchecked"})
public class ListLoopTest {

	/**
	 * 初始化 list，添加n个元素
	 *
	 * @param list
	 * @return
	 */
	public static <T> List initList(List list, int n) {
		for (int i = 0; i < n; i++)
			list.add(i);
		return list;
	}

	/**
	 * 遍历 list，判断是否实现 RandomAccess 接口来使用不同的遍历方法
	 *
	 * @param list
	 */
	public static void accessList(List list) {
		long startTime = System.currentTimeMillis();

		if (list instanceof RandomAccess) {
			System.out.println("实现了 RandomAccess 接口...");
			for (int i = 0; i < list.size(); i++) {
				list.get(i);
			}
		} else {
			System.out.println("没实现 RandomAccess 接口...");
			for (Iterator iterator = list.iterator(); iterator.hasNext();) {
				iterator.next();
			}
		}

		long endTime = System.currentTimeMillis();
		System.out.println("遍历时间：" + (endTime - startTime));
	}

	/**
	 * loop 遍历 list
	 */
	public static void accessListByLoop(List list) {
		long startTime = System.currentTimeMillis();

		for (int i = 0; i < list.size(); i++) {
			list.get(i);
		}

		long endTime = System.currentTimeMillis();
		System.out.println("loop遍历时间：" + (endTime - startTime));
	}

	/**
	 * 迭代器遍历
	 */
	public static void accessListByIterator(List list) {
		long startTime = System.currentTimeMillis();

		for (Iterator iterator = list.iterator(); iterator.hasNext();) {
			iterator.next();
		}

		long endTime = System.currentTimeMillis();
		System.out.println("Iterator遍历时间：" + (endTime - startTime));
	}

	public static void main(String[] args) {
		ArrayList<Integer> aList = (ArrayList<Integer>) initList(new ArrayList<>(), 2000000);
		LinkedList<Integer> lList = (LinkedList<Integer>) initList(new LinkedList<>(), 50000);

		accessList(aList);
		accessList(lList);

		System.out.println("ArrayList");
		accessListByLoop(aList);
		accessListByIterator(aList);

		System.out.println("LinkedList");
		accessListByLoop(lList);
		accessListByIterator(lList);
	}

  /*
  实现了 RandomAccess 接口...
  遍历时间：8
  没实现 RandomAccess 接口...
  遍历时间：2
  ArrayList
  loop遍历时间：5
  Iterator遍历时间：8
  LinkedList
  loop遍历时间：1532
  Iterator遍历时间：1
  */
}
```
