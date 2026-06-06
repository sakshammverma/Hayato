def classify_risk(filename: str) -> str:
    high = ["auth", "crypto", "payment", "admin", "security", "login", "password", "token"]
    low  = ["test_", "_test", "readme", "docs/", ".md"]

    filename_lower = filename.lower()

    if any(keyword in filename_lower for keyword in high):
        return "high"
    if any(keyword in filename_lower for keyword in low):
        return "low"
    return "medium"