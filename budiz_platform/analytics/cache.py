from django.core.cache import cache

CACHE_PREFIX = "dashboard_workspace_"


def invalidate_workspace_cache(workspace_id):
    """
    Invalidate all cached dashboard keys for a workspace.
    """
    pattern = f"{CACHE_PREFIX}{workspace_id}_*"

    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(pattern)
        return

    if hasattr(cache, "keys"):
        keys = cache.keys(pattern)
        for key in keys:
            cache.delete(key)
        return

    # Fallback for cache backends without key iteration support (e.g., LocMemCache).
    return
