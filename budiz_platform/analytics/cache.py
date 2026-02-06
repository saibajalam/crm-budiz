from django.core.cache import cache

CACHE_PREFIX = "dashboard_workspace_"


def invalidate_workspace_cache(workspace_id):
    """
    Invalidate all cached dashboard keys for a workspace.
    """
    keys = cache.keys(f"{CACHE_PREFIX}{workspace_id}_*")
    for key in keys:
        cache.delete(key)
