from django.contrib import admin
from .models import *


class UserAdmin(admin.ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "username",
        "phone",
        "email",
        "is_active",
        "is_staff",
        "is_admin",
        "is_superuser",
    ]
    list_editable = ["is_active", "is_staff", "is_admin", "is_superuser"]
    search_fields = ["first_name", "last_name", "username", "email", "phone"]
    list_filter = ["is_active", "is_staff", "is_admin", "is_superuser"]
    list_display_links = ["first_name", "last_name", "username", "email"]
    list_per_page = 20


class ContactAdmin(admin.ModelAdmin):
    list_display = [ "email", "created_at"]
    search_fields = ["email"]
    list_filter = ["created_at", "email"]
    list_display_links = ["email"]
    list_per_page = 20


admin.site.register(User, UserAdmin)
admin.site.register(Profile)
admin.site.register(Contact, ContactAdmin)
