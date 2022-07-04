# blog-hugo

[![Build Status](https://travis-ci.com/ld000/blog-hugo.svg?branch=master)](https://travis-ci.com/ld000/blog-hugo)

```sh
# add theme
git submodule add https://github.com/budparr/gohugo-theme-ananke.git themes/ananke
echo 'theme = "ananke"' >> config.toml

# update theme
git submodule update --rebase --remote

# add post
hugo new posts/my-first-post.md

# dev
hugo server -D
hugo serve -t  hugo-theme-cleanwhite
```