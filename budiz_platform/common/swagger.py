from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

workspace_header = OpenApiParameter(
    name="X-Workspace-ID",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.HEADER,
    required=False,
    description="Workspace ID for multi-tenant isolation",
)
