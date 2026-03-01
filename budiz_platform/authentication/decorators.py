from rest_framework.response import Response


def role_required(role_name):
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.has_role(
                role_name
            ):
                return Response({"error": "Forbidden"}, status=403)
            return func(self, request, *args, **kwargs)

        return wrapper

    return decorator
