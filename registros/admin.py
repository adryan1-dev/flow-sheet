from django.contrib import admin
from .models import Registro


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "email", "telefone", "status", "executado_em")
    list_filter = ("status",)
    search_fields = ("nome", "empresa", "email")
