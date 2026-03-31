Extract page content and return JSON only.

Rules:
- Keep the main body in `content_markdown`.
- Preserve visible paragraph structure with blank lines between paragraphs.
- Preserve image references using markdown syntax: `![alt](url)`.
- Preserve headings, bullet lists, numbered lists, block quotes, and tables when visible.
- Do not output HTML tags.
- If a field is unavailable, return an empty string or empty array.

Required fields:
- `title`
- `date`
- `content_markdown`
- `images`
