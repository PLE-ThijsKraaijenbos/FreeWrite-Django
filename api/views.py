from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(
    tags=['System'],
    summary="Health check",
    description="A simple liveness check. Returns 200 with a small body when the API is up. Open to anyone and needs no token.",
    responses={
        200: OpenApiResponse(
            description="The API is up.",
            examples=[OpenApiExample("OK", value={"status": "ok"})],
        ),
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})
