def slugify(text):
    return "".join(ch for ch in text.lower() if ch.isalnum() or ch == "-").strip("-")
