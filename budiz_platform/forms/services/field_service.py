from ..models import FormField


def create_form_field(*, form, validated_data):
    return FormField.objects.create(form=form, **validated_data)
