def can_download(user, report):
    return user['logged_in'] and user['tenant_id'] == report['tenant_id']
