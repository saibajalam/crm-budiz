import json
import urllib.request
import urllib.error


def execute(payload, params, workspace, user):
    """
    Send a webhook.
    params = {"url": "https://example.com", "method": "POST", "body": {...}, "headers": {...}}
    """
    url = params.get("url")
    if not url:
        return False

    method = params.get("method", "POST").upper()
    body = params.get("body", payload)
    headers = params.get("headers", {})

    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **headers},
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=5):
            return True
    except urllib.error.URLError:
        return False
