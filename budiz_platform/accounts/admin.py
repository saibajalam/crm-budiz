from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, UserRole
from .forms import UserCreationForm


class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    model = User

    list_display = ("email", "full_name", "is_active")
    list_filter = ("is_active",)

    fieldsets = (
    (None, {"fields": ("email", "password")}),
    ("Personal info", {"fields": ("full_name",)}),
    ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )

    add_fieldsets = (
    (None, {
        "classes": ("wide",),
        "fields": ("email", "full_name", "password1", "password2", "is_active", "is_staff", "is_superuser"),
    }),
    )


    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
admin.site.register(Role)
admin.site.register(UserRole)
