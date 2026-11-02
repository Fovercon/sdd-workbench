def mask_identifier(value):
    return '****' + value[-4:]


def export_row(value):
    return {'identifier': mask_identifier(value)}


def audit_label(value):
    return 'audit:' + mask_identifier(value)


def sum_counts(values):
    return sum(values)
