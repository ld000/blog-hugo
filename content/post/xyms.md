---
title: 响应模式
date: 2016-12-20
tags: ["html"]
---
# 常见响应模式
- 大体流动模型(mostly fluid)
- 掉落列模型(column drop)
- 活动布局模型(layout shifter)
- 画布溢出模型(off canvas)

<!--more-->

## 掉落列模型

```css
<div class="container">
  <div class="box dark_blue"></div>
  <div class="box light_blue"></div>
  <div class="box green"></div>
</div>

.container {
  display: flex;
  flex-wrap: wrap;
}

.box {
  width: 100%;
}

@media screen and (min-width: 450px) {
  .dark-blue {
    width: 25%;
  }

  .light-blue {
    width: 75%;
  }
}

@media screen and (min-width: 550px) {
  .dark-blue,
  .green {
    width: 25%;
  }

  .light-blue {
    width: 50%;
  }
}
```

## 大体流动模型

```css
<div class="container">
  <div class="box dark_blue"></div>
  <div class="box light_blue"></div>
  <div class="box green"></div>
  <div class="box red"></div>
  <div class="box orange"></div>
</div>

.container {
  display: flex;
  flex-wrap: wrap;
}

.box {
  width: 100%;
}

@media screen and (min-width: 450px) {
  .light-blue,
  .green {
    width: 50%;
  }
}

@media screen and (min-width: 550px) {
  .dark-blue,
  .light-blue {
    width: 50%;
  }

  .red,
  .green,
  .orange {
    width: 33.333333%;
  }
}

@media screen and (min-width: 700px) {
  .container {
    width: 700px;
    margin-left: auto;
    margin-right: auto;
  }
}
```

## 活动布局模型
```css
<div class="container">
  <div class="box dark_blue"></div>
  <div class="container" id="container2">
    <div class="box light_blue"></div>
    <div class="box green"></div>
  </div>
  <div class="box red"></div>
</div>

.container {
  width: 100%;  /* .ddd */
  display: flex;
  flex-wrap: wrap;
}

.box {
  width: 100%;
}

@media screen and (min-width: 500px) {
  .dark-blue {
    width: 50%;
  }
  #container2 {
    width: 50%;
  }
}

@media screen and (min-width: 600px) {
  .dark-blue {
    width: 25%;
    order: 1;
  }
  #container2 {
    width: 50%;
  }
  .red {
    width: 25%;
    order: -1;
  }
}
```

## 画布溢出模型

```html
<!DOCTYPE html>
<!-- saved from url=(0070)http://udacity.github.io/RWDF-samples/Lesson4/patterns/off-canvas.html -->
<html lang="en"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title></title>
    <link rel="stylesheet" type="text/css" href="./off-canvas_files/default-styles.css">
    <style type="text/css">

      html, body {
        height: 100%;
        width: 100%;
      }
      a#menu svg {
        width: 40px;
        fill: #000;
      }
      nav, main {
        padding: 1em;
        box-sizing: border-box;
      }
      main {
        width: 100%;
        height: 100%;
      }


      /*
       * Off-canvas layout styles.
       */

      /* Since we're mobile-first, by default, the drawer is hidden. */
      nav {
        width: 300px;
        height: 100%;
        position: absolute;
        /* This trasform moves the drawer off canvas. */
        -webkit-transform: translate(-300px, 0);
        transform: translate(-300px, 0);
        /* Optionally, we animate the drawer. */
        transition: transform 0.3s ease;
      }
      nav.open {
        -webkit-transform: translate(0, 0);
        transform: translate(0, 0);
      }

      /* If there is enough space (> 600px), we keep the drawer open all the time. */
      @media (min-width: 600px) {

        /* We open the drawer. */
        nav {
          position:relative;
          -webkit-transform: translate(0, 0);
          transform: translate(0, 0);
        }

        /* We use Flexbox on the parent. */
        body {
          display: -webkit-flex;
          display: flex;
          -webkit-flex-flow: row nowrap;
          flex-flow: row nowrap;
        }

        main {
          width: auto;
          /* Flex-grow streches the main content to fill all available space. */
          flex-grow: 1;
        }
      }

      /* If there is space (> 800px), we keep the drawer open by default. */
      @media (min-width: 600px) {
        main > #menu:after {
          content: 'The drawer stays open if width > 600px';
        }
        main p, nav p {
          text-decoration: line-through;
        }
      }

    </style>
  <link rel="import" href="chrome-extension://melpgahbngpgnbhhccnopmlmpbmdaeoi/app/templates/feedback.html" id="udacity-test-widget"><script id="ud-grader-options">UdacityFEGradingEngine.turnOn();</script></head>
  <body>
    <nav id="drawer" class="dark_blue">
      <h2>Off Canvas</h2>
      <p>Click outside the drawer to close</p>
    </nav>

    <main class="light_blue">
      <a id="menu">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
          <path d="M2 6h20v3H2zm0 5h20v3H2zm0 5h20v3H2z"></path>
        </svg>
      </a>
      <p>Click on the menu icon to open the drawer</p>
    </main>

    <script>
      /*
       * Open the drawer when the menu ison is clicked.
       */
      var menu = document.querySelector('#menu');
      var main = document.querySelector('main');
      var drawer = document.querySelector('#drawer');

      menu.addEventListener('click', function(e) {
        drawer.classList.toggle('open');
        e.stopPropagation();
      });
      main.addEventListener('click', function() {
        drawer.classList.remove('open');
      });

    </script><script src="chrome-extension://melpgahbngpgnbhhccnopmlmpbmdaeoi/app/js/libs/GE.js" id="udacity-front-end-feedback"></script><test-widget></test-widget></body></html>
```

```css
@import url(https://fonts.googleapis.com/css?family=Roboto);

html, body {
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Roboto', sans-serif;
}

.title {
  font-size: 2.5em;
  text-align: center;
}

.box {
  min-height: 150px;
}

.dark_blue {
  background-color: #2A457A;
  color: #efefef;
}

.light_blue {
  background-color: #099DD9;
}

.green {
  background-color: #0C8542;
}

.lime {
  background-color: rgb(179, 210, 52);
}

.seafoam {
  background-color: rgb(77, 190, 161);
}

.red {
  background-color: #EC1D3B;
}

.orange {
  background-color: #F79420;
}
```
