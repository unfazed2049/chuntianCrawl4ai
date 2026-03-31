def pick_markdown_content(markdown_obj) -> str:
    """Prefer raw markdown so images and full structure are preserved."""
    if not markdown_obj:
        return ""
    raw = getattr(markdown_obj, "raw_markdown", "") or ""
    fit = getattr(markdown_obj, "fit_markdown", "") or ""
    return raw or fit
