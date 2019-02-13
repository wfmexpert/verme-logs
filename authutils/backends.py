def set_user_login_details(request, attr_name, was_found):
    if request is None:
        return
    if not hasattr(request, 'login_details'):
        setattr(request, 'login_details', {})
    details = request.login_details
    details['user_found'] = details.get('user_found', False) or was_found
    details['user_found_by_' + attr_name] = was_found
