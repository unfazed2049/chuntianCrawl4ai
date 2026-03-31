Extract news page content and return JSON only.

Rules:
- Put the full article body in `content_markdown`.
- Keep paragraph breaks (blank line between paragraphs).
- Preserve image references as markdown `![alt](url)`.
- Preserve headings and list structure.
- Do not output HTML tags.

Required fields:
- `title`
- `date`
- `content_markdown`
- `images`
