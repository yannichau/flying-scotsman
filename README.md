# Green skies and blue grass

Welcome to **Green skies and blue grass**, a personal Jekyll-based blog and interactive site exploring alternative perspectives, travel, technology, and creative writings.

## Site Overview

- **Title**: Green skies and blue grass
- **Live URL**: [https://yannichau.github.io/flying-scotsman](https://yannichau.github.io/flying-scotsman)
- **Author / Maintainer**: Yanni Chau
- **Theme**: Minima (customized with unique interactive elements and dynamic CSS styling)

---

## Key Features & Layout

- **Interactive Dynamic Background**: Features a custom dynamic tube/line background rendered via D3.js (`index.html`) matching the central blog feed layout.
- **Image Carousels & Galleries**: Responsive media layout with custom asset optimization and styling.
- **Blog Posts & Archive**: Structured using Jekyll's standard collections (`_posts`, `_pages`, `_archive`).

---

## Local Development Setup

To run or develop this site locally, make sure you have Ruby and Bundler installed.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yannichau/flying-scotsman.git
   cd my-awesome-site
   ```

2. **Install dependencies**:
   ```bash
   bundle install
   ```

3. **Run the Jekyll development server**:

   Kill existing jekyll processes first.
   ```bash
   pkill -f jekyll
   ```

   Run the following to serve on a local computer

   ```bash
   bundle exec jekyll serve
   ```

   Alternatively, when running from tailscale, run the following two commands. Firstly, deploy specifically on local host:
   ```bash
   bundle exec jekyll serve --host 127.0.0.1 --livereload
   ```

   Then, to proxy Jekyll to a secure secondary port on the network, run the following. The website will be viewable at https://<ts.net>:4433/flying-scotsman/
   ```bash
   tailscale serve --bg --https=4433 localhost:4000
   ```


4. Open your browser at `http://localhost:4000/flying-scotsman/`. On tailscale that would be `<tailscale-ip>:4000/flying-scotsman/`

5. Quick commands
```bash
rclip <url-or-image-path>  # find closest matching image in current working directory
xviewer <image-path>  # quickly open image
avifenc <original-image.png> <compressed-image.avif>
```

---

## Project Structure

- `_posts/` — Markdown files for blog posts.
- `_pages/` — Static standalone pages.
- `_layouts/` — HTML layout templates.
- `assets/` — Stylesheets, JavaScript files, and images.
- `index.html` — The main entry point featuring the dynamic interactive layout and blog feed.
- `_config.yml` — Jekyll global configuration settings.

---

## Connect & Socials

- [LinkedIn](https://www.linkedin.com/in/yanni-chau-a52b61195)
- [GitHub](https://github.com/yannichau)
- [YouTube](https://www.youtube.com/@cluelessyanni5664)
- [Medium](https://medium.com/@yannichau/about)
