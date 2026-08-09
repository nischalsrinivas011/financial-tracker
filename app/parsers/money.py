def rupees_to_paise(text: str) -> int:
    """Parse a statement amount like '213,985.00' or '-689.30' into integer paise.

    String-based on purpose: money is never routed through float() (rule 1).
    """
    text = text.replace(",", "").strip()
    if not text:
        return 0

    negative = text.startswith("-")
    if negative:
        text = text[1:]

    rupees, _, paise = text.partition(".")
    paise = (paise + "00")[:2]
    value = int(rupees) * 100 + int(paise)
    return -value if negative else value
