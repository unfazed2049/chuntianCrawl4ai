Extract product page content and return JSON only.

Rules:
- Put detailed page text in `content_markdown`.
- Keep paragraph formatting and list structure.
- Preserve image references in markdown `![alt](url)`.
- Do not output HTML tags.

Required fields:
- `title`
- `date`
- `content_markdown`
- `images`
