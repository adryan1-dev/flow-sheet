from django.urls import path

from .views import (
    detalhe_execucao_view,
    executar_automacao_view,
    reprocessar_erros_view,
    status_execucao_view,
)

app_name = "automations"

urlpatterns = [
    path("executar/", executar_automacao_view, name="executar"),
    path("execucoes/<int:execution_id>/", detalhe_execucao_view, name="detalhe_execucao"),
    path("execucoes/<int:execution_id>/status/", status_execucao_view, name="status_execucao"),
    path(
        "execucoes/<int:execution_id>/reprocessar-erros/",
        reprocessar_erros_view,
        name="reprocessar_erros",
    ),
]
