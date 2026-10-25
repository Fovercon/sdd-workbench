# Synthetic fixture; no production implementation or validation claim.
def select(items, key):
    return [item for item in items if item['id'] == key]
