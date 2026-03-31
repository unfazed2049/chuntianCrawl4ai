Extract page content for downstream indexing and return JSON only.

Rules:
- Keep the full page body in `content_markdown`.
- Preserve image references in markdown `![alt](url)`.
- Preserve paragraph breaks, headings, and list/table structure.
- Do not output HTML tags.

Required fields:
- `title`
- `date`
- `content_markdown`
- `images`
