from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from automations.models import Execution
from registros.models import Registro

from .services import iniciar_automacoes_em_background


def executar_automacao_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    target_url = request.build_absolute_uri(reverse("form_teste"))
    execution = iniciar_automacoes_em_background(target_url=target_url, user=request.user)

    return redirect(f"{reverse('listar_registros')}?execution_id={execution.id}")


def detalhe_execucao_view(request, execution_id):
    execution = get_object_or_404(
        Execution.objects.select_related("importacao"),
        pk=execution_id,
    )
    resultados = execution.resultados.select_related("registro").order_by("id")

    return render(
        request,
        "automations/detalhe_execucao.html",
        {
            "execution": execution,
            "resultados": resultados,
            "pode_reprocessar_erros": execution.resultados.filter(status="erro").exists(),
            "status_api_url": reverse("automations:status_execucao", args=[execution.id]),
        },
    )


def reprocessar_erros_view(request, execution_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    execution = get_object_or_404(Execution, pk=execution_id)
    registros = list(
        Registro.objects.filter(
            resultados_execucao__execution=execution,
            resultados_execucao__status="erro",
        ).distinct()
    )

    target_url = request.build_absolute_uri(reverse("form_teste"))
    nova_execucao = iniciar_automacoes_em_background(
        target_url=target_url,
        user=request.user,
        registros=registros,
        importacao=execution.importacao,
    )

    return redirect("automations:detalhe_execucao", execution_id=nova_execucao.id)


def status_execucao_view(request, execution_id):
    execution = get_object_or_404(
        Execution.objects.select_related("importacao"),
        pk=execution_id,
    )
    registros = (
        execution.importacao.registros.all().order_by("id")
        if execution.importacao is not None
        else Registro.objects.none()
    )
    resultados = execution.resultados.select_related("registro").order_by("id")

    return JsonResponse(
        {
            "execution": {
                "id": execution.id,
                "status": execution.status,
                "status_display": execution.get_status_display(),
                "linhas_processadas": execution.linhas_processadas,
                "total_linhas": execution.total_linhas,
                "sucesso_count": execution.sucesso_count,
                "erro_count": execution.erro_count,
                "finalizado_em": execution.finalizado_em.isoformat() if execution.finalizado_em else "",
                "is_finished": execution.status in {"completed", "error"},
            },
            "registros": [
                {
                    "id": registro.id,
                    "status": registro.status,
                    "status_display": registro.get_status_display(),
                    "mensagem_erro": registro.mensagem_erro,
                }
                for registro in registros
            ],
            "resultados": [
                {
                    "registro_id": resultado.registro_id,
                    "registro_nome": resultado.registro.nome,
                    "registro_email": resultado.registro.email,
                    "status": resultado.status,
                    "status_display": resultado.get_status_display(),
                    "mensagem_erro": resultado.mensagem_erro,
                    "executado_em": resultado.executado_em.strftime("%d/%m/%Y %H:%M:%S"),
                }
                for resultado in resultados
            ],
            "mostrar_coluna_erro": any(registro.mensagem_erro for registro in registros),
        }
    )
