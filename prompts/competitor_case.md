Extract page content for downstream indexing and return JSON only.

Rules:
- Keep the main text in `content_markdown`.
- Preserve image references in markdown `![alt](url)`.
- Keep paragraph formatting and list structure.
- Do not output HTML tags.

Required fields:
- `title`
- `date`
- `content_markdown`
- `images`
