def has_permission(user_permissions: list[str], required_perm: str) -> bool:
    """
    Checks if the required permission exists in the user's permission list.
    Supports wildcards like 'users:*'.
    """
    # 1. Direct match
    if required_perm in user_permissions:
        return True
    
    # 2. Wildcard match (e.g., 'users:*' matches 'users:create')
    if ":" in required_perm:
        resource = required_perm.split(":")[0]
        wildcard_perm = f"{resource}:*"
        if wildcard_perm in user_permissions:
            return True
            
    return False