def select_retry(records):
    return [r["id"] for r in records if r["state"] in ("failed", "succeeded")]


def progress(records):
    if not records:
        return 100
    return round(sum(r["state"] == "succeeded" for r in records) * 100 / len(records))
