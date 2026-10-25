def normalize_label(value):
    return value.strip()


def unique_labels(values):
    return [normalize_label(value) for value in values]
