Extract page content for downstream indexing and return JSON only.

Rules:
- Put the main article text in `content_markdown`.
- Preserve image references as markdown `![alt](url)`.
- Preserve paragraph structure with blank lines between paragraphs.
- Preserve headings and list structure.
- Do not output HTML tags.

Required fields:
- `title`
- `date`
- `content_markdown`
- `images`
