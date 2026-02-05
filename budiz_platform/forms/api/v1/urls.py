from django.urls import path
from .views import (
    PublicFormSubmitAPIView,
    CreateFormAPIView,
    AddFieldAPIView,
    UpdateFormAssignmentAPIView,
    FormConversionFunnelAPIView,
    FormEmbedAPIView,
)

urlpatterns = [
    path("forms/submit/", PublicFormSubmitAPIView.as_view(), name="public_form_submit"),
    path("forms/create/", CreateFormAPIView.as_view(), name="create_form"),
    path(
        "forms/<int:form_id>/add-field/",
        AddFieldAPIView.as_view(),
        name="add_form_field",
    ),
    path(
        "forms/<int:form_id>/update-assignment/",
        UpdateFormAssignmentAPIView.as_view(),
        name="update_form_assignment",
    ),
    path(
        "forms/<int:form_id>/funnel/",
        FormConversionFunnelAPIView.as_view(),
        name="form_conversion_funnel",
    ),
    path("forms/<int:form_id>/embed/", FormEmbedAPIView.as_view(), name="form_embed"),
]

app_name = "forms"
