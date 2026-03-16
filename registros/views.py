from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from automations.models import Execution

from .models import ImportacaoPlanilha, Registro
from .services import importar_planilha


def upload_planilha(request):

    if request.method == "POST":

        arquivo = request.FILES["planilha"]

        importar_planilha(arquivo)

        return redirect("listar_registros")

    return render(request, "upload.html")

def listar_registros(request):
    ultima_importacao = ImportacaoPlanilha.objects.order_by("-criado_em").first()
    registros = list(ultima_importacao.registros.all()[:50]) if ultima_importacao else []
    execution_id = request.GET.get("execution_id")
    ultima_execucao = (
        Execution.objects.filter(importacao=ultima_importacao).order_by("-criado_em").first()
        if ultima_importacao
        else Execution.objects.order_by("-criado_em").first()
    )
    if execution_id:
        ultima_execucao = get_object_or_404(Execution, pk=execution_id)
    mostrar_coluna_erro = any(registro.mensagem_erro for registro in registros)

    return render(request, "lista_registros.html", {
        "registros": registros,
        "ultima_importacao": ultima_importacao,
        "ultima_execucao": ultima_execucao,
        "mostrar_coluna_erro": mostrar_coluna_erro,
        "status_api_url": (
            reverse("automations:status_execucao", args=[ultima_execucao.id])
            if ultima_execucao
            else ""
        ),
    })


def editar_registro(request, registro_id):
    registro = get_object_or_404(Registro, pk=registro_id)

    if request.method == "POST":
        registro.nome = request.POST.get("nome", "").strip()
        registro.empresa = request.POST.get("empresa", "").strip()
        registro.email = request.POST.get("email", "").strip()
        registro.telefone = request.POST.get("telefone", "").strip()
        registro.status = Registro.STATUS_PENDENTE
        registro.mensagem_erro = ""
        registro.executado_em = None
        registro.save(
            update_fields=[
                "nome",
                "empresa",
                "email",
                "telefone",
                "status",
                "mensagem_erro",
                "executado_em",
            ]
        )
        return redirect("listar_registros")

    return render(request, "editar_registro.html", {"registro": registro})


def form_teste(request):

    if request.method == "POST":

        dados = {
            "nome": request.POST.get("nome"),
            "empresa": request.POST.get("empresa"),
            "email": request.POST.get("email"),
            "telefone": request.POST.get("telefone"),
        }

        return render(request, "form_resultado.html", dados)

    return render(request, "form_teste.html")
