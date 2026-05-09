# Repository Guidelines

## Startup Routine
Read all files in context/ - this is your foundation 

Read MEMORY.md - this is what you've learned over time
Use both to shape every task

Memory System
When I correct you or you learn something new, update the relevant section in MEMORY.md:

Voice - tone, phrasing, writing corrections

Process - how I want tasks done

People - who people are, relationships 

Projects - active work, current tasks, status 

Output - formats, naming, delivery preferences

Tools - which tools to use and how

Keep MEMORY.md current. When something changes, update it in place - replace outdated info, don't just append below it. The file should always reflect the latest state.

## Project Overview

This is a personal blog built with Hugo and deployed to GitHub Pages through GitHub Actions. The active Hugo config lives under `config/_default/`, with `config/_default/hugo.toml` currently selecting the `blowfish` theme.

## Important Directories

- `content/`: authored Markdown content. Blog posts are primarily in `content/posts/`; weekly Spring notes are in `content/springweek/`.
- `static/`: files copied directly into the generated site, including images and domain/static assets.
- `config/_default/`: Hugo site, theme, language, menu, markup, and parameter configuration.
- `archetypes/`: Hugo content templates used by `hugo new`.
- `.github/workflows/`: GitHub Actions deployment workflow.
- `themes/`: vendored/submodule theme code. Treat this as upstream theme code unless the task explicitly asks for theme changes.
- `public/` and `resources/`: generated output/cache directories. Do not edit or commit generated files unless explicitly requested.

## Local Development

Use Hugo Extended. The GitHub Actions workflow currently pins Hugo `0.161.1`.

Common commands:

```bash
hugo server -D
hugo --gc --minify
hugo new posts/my-new-post.md
```

Before finishing changes that affect rendering or configuration, run:

```bash
hugo --gc --minify
```

For content-only edits, a full build is still preferred when practical because Hugo front matter errors are easy to miss.

## Content Conventions

- Markdown content uses YAML front matter delimited by `---`.
- New posts should normally be created under `content/posts/`.
- The default archetype creates draft posts; keep `draft: true` for unfinished drafts and set it to `false` or remove it only when publishing.
- Prefer colocated page bundles such as `content/posts/<slug>/index.md` when a post has many local assets.
- Existing older posts often reference images from `/img/...`; preserve working paths unless intentionally reorganizing assets.
- Keep article edits focused. Do not rewrite author voice, titles, dates, tags, or slugs unless the task asks for it.

## Configuration Notes

- Site-wide behavior is configured in `config/_default/*.toml`.
- Deployment builds on pushes to `master` using `.github/workflows/deploy.yml`.
- `baseURL` handling differs between local config and GitHub Pages workflow; be careful when changing either.
- `deploy.sh` is an older/manual subtree deployment helper. Prefer the GitHub Actions workflow unless the task specifically targets manual deployment.

## Editing Rules For Agents

- Do not modify `themes/` unless the user explicitly asks for theme-level changes.
- Do not edit generated `public/` output as source.
- Do not overwrite existing user changes. Check `git status --short` before editing when making non-trivial changes.
- Keep generated caches, build artifacts, and local server output out of commits.
- If changing menus, languages, theme params, or URLs, verify the site builds and inspect the relevant config files together.
- If adding assets, use stable, lowercase, URL-friendly file names where possible.

## Git And Deployment

- The main branch is `master`.
- GitHub Pages deployment is handled by `.github/workflows/deploy.yml`.
- The production build command in CI is effectively:

```bash
hugo --gc --minify --baseURL "${{ steps.pages.outputs.base_url }}/"
```

Do not make deployment credential or repository settings changes from code unless explicitly requested.
