from django.contrib import admin
from .models import Execution, ResultadoExecucaoRegistro


@admin.register(Execution)
class ExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "importacao",
        "status",
        "total_linhas",
        "linhas_processadas",
        "sucesso_count",
        "erro_count",
        "criado_em",
        "finalizado_em",
    )
    list_filter = ("status",)


@admin.register(ResultadoExecucaoRegistro)
class ResultadoExecucaoRegistroAdmin(admin.ModelAdmin):
    list_display = ("execution", "registro", "status", "executado_em")
    list_filter = ("status",)
