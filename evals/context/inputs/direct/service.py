def select(items, key):
    return [item for item in items if key in item['id']]
