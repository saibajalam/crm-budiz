from rest_framework.response import Response


def api_response(data=None, message="", success=True, error=False, status_code=200):
    payload = {
        "success": success,
        "data": data,
        "message": message,
        "error": error,
    }
    return Response(payload, status=status_code)
