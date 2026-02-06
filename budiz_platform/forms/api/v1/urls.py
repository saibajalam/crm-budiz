from django.urls import path
from .views import (
    PublicFormSubmitAPIView,
    CreateFormAPIView,
    AddFieldAPIView,
    UpdateFormAssignmentAPIView,
    FormEmbedAPIView,
)

urlpatterns = [
    path(
        "public/forms/<slug:slug>/submit/",
        PublicFormSubmitAPIView.as_view(),
        name="public-form-submit",
    ),
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
    path("forms/<int:form_id>/embed/", FormEmbedAPIView.as_view(), name="form_embed"),
]

app_name = "forms"
