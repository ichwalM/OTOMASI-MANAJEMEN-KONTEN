---
name: wordpress-manager
description: Manage and publish content to WordPress via REST API. Create, edit, list, and delete WordPress posts or pages directly from chat commands.
version: 1.0.0
author: Antigravity
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [CMS, WordPress, Publishing, Content]
---

# WordPress Manager Skill

This skill allows Hermes to interact directly with the local or remote WordPress website using the REST API through the helper script `wp_manager.py`.

## Environment Variables
The script automatically reads the following environment variables if set (or they can be passed as CLI arguments):
- `WORDPRESS_URL`: WordPress base URL (inside Docker network, this is `http://wordpress:80` or `http://wordpress`).
- `WORDPRESS_USER`: WordPress username with publishing rights (e.g., `admin`).
- `WORDPRESS_APP_PASSWORD`: WordPress Application Password created in the WordPress admin profile.

The helper script is located at:
`/opt/data/skills/wordpress-manager/scripts/wp_manager.py`
(or `./hermes/skills/wordpress-manager/scripts/wp_manager.py` relative to project root).

---

## When to Use This Skill
Activate this skill whenever the user asks via Telegram to:
- Write, draft, or publish a new article/post on WordPress.
- Update or edit an existing article/post.
- List recent articles or search for existing posts.
- Delete, trash, or unpublish an article.
- Check the status or get the link to an existing post.

---

## Instructions for Hermes

### 1. Creating a New Post
When the user says something like:
*"Buat postingan tentang Tips Belajar Python..."* or *"Tolong tulis artikel baru..."*

1. **Generate High-Quality Content**: Draft a comprehensive, well-structured article formatted in clean HTML (use `<h2>`, `<h3>`, `<p>`, `<ul>`, `<li>`, `<blockquote>` tags).
2. **Execute Command**:
   ```bash
   python3 /opt/data/skills/wordpress-manager/scripts/wp_manager.py create-post \
     --title "Judul Artikel" \
     --content "<h2>Pengantar</h2><p>Isi artikel...</p>" \
     --status publish
   ```
   *(Use `--status draft` if the user specifically asked for a draft).*

   > **Pitfall (HTML Shell Quoting):** Rich HTML content often contains nested quotes (`"`, `'`), dollar signs, or newlines that break raw shell command strings. When passing multi-paragraph HTML or content with quotes, invoke `wp_manager.py` via Python `subprocess.run([...])` rather than raw bash CLI string interpolation to prevent syntax errors and truncated bodies.
3. **Reply to the User**: Confirm publication, provide the post ID, title, and the full URL link (`http://localhost:10000/?p=...` or post permalink).

---

### 2. Creating or Publishing a Page (Landing Page / Custom Page)
When the user asks to create an e-commerce page, landing page, or custom standalone page on WordPress:
1. **Pages vs. Posts**: Use the WordPress Pages REST endpoint (`/wp-json/wp/v2/pages`) or `create-page` for static pages, storefronts, or about pages.
2. **Custom HTML & Styles**: To render custom HTML/CSS without WordPress theme interference or auto-formatting mangling, wrap content inside Gutenberg HTML comments:
   ```html
   <!-- wp:html -->
   <style>...</style>
   <div class="custom-layout">...</div>
   <script>...</script>
   <!-- /wp:html -->
   ```
3. **Local & External URL Mapping**:
   - Internal Docker API URL: `http://wordpress:80` (used by Hermes).
   - User-facing Host URL: `http://localhost:10000/<slug>/` (the public link the user opens in their browser).
   Always report the `http://localhost:10000/...` link to the user.

---

### 3. Updating an Existing Post or Page
When the user says something like:
*"Ubah postingan ID 15, tambahkan bagian kesimpulan..."* or *"Update judul postingan 10..."*

1. **Check Existing Post First** (if needed):
   ```bash
   python3 /opt/data/skills/wordpress-manager/scripts/wp_manager.py get-post --id 15
   ```
2. **Execute Update**:
   ```bash
   python3 /opt/data/skills/wordpress-manager/scripts/wp_manager.py update-post \
     --id 15 \
     --title "Judul Baru" \
     --content "<p>Konten yang diperbarui...</p>"
   ```
3. **Reply to the User**: Confirm the update was applied successfully with the updated URL.

---

### 4. Listing Posts
When the user asks:
*"Tampilkan daftar artikel terakhir..."* or *"Ada postingan apa saja di web?"*

1. **Execute List Command**:
   ```bash
   python3 /opt/data/skills/wordpress-manager/scripts/wp_manager.py list-posts --limit 5
   ```
2. **Format Response**: Present the list clearly in Telegram (Title, ID, Status, and URL).

---

### 5. Deleting a Post
When the user asks:
*"Hapus postingan ID 12"*

1. **Execute Delete Command**:
   ```bash
   python3 /opt/data/skills/wordpress-manager/scripts/wp_manager.py delete-post --id 12
   ```
2. **Reply to the User**: Confirm that the post has been moved to trash or deleted.
