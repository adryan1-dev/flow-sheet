from threading import Thread

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone
from playwright.sync_api import sync_playwright

from automations.models import Execution, ResultadoExecucaoRegistro
from registros.models import ImportacaoPlanilha, Registro


def executar_automacoes(*, target_url, user=None, registros=None, importacao=None):
    execution, registro_ids = _criar_execucao(
        target_url=target_url,
        user=user,
        registros=registros,
        importacao=importacao,
    )
    _processar_execucao(execution_id=execution.id, registro_ids=registro_ids, target_url=target_url)
    execution.refresh_from_db()
    return execution


def iniciar_automacoes_em_background(*, target_url, user=None, registros=None, importacao=None):
    execution, registro_ids = _criar_execucao(
        target_url=target_url,
        user=user,
        registros=registros,
        importacao=importacao,
    )

    if not registro_ids:
        return execution

    thread = Thread(
        target=_processar_execucao_em_background,
        kwargs={
            "execution_id": execution.id,
            "registro_ids": registro_ids,
            "target_url": target_url,
        },
        daemon=True,
    )
    thread.start()
    return execution


def _criar_execucao(*, target_url, user=None, registros=None, importacao=None):
    if registros is None:
        importacao = importacao or ImportacaoPlanilha.objects.order_by("-criado_em").first()
        registros = list(importacao.registros.all().order_by("id")) if importacao else []
    else:
        registros = list(registros)
        if importacao is None and registros:
            importacao = registros[0].importacao

    execution = Execution.objects.create(
        importacao=importacao,
        user=user if getattr(user, "is_authenticated", False) else None,
        status="running",
        total_linhas=len(registros),
        target_url=target_url,
    )

    if not registros:
        execution.status = "completed"
        execution.finalizado_em = timezone.now()
        execution.save(update_fields=["status", "finalizado_em"])

    return execution, [registro.id for registro in registros]


def _processar_execucao_em_background(*, execution_id, registro_ids, target_url):
    close_old_connections()
    try:
        _processar_execucao(execution_id=execution_id, registro_ids=registro_ids, target_url=target_url)
    finally:
        close_old_connections()


def _processar_execucao(*, execution_id, registro_ids, target_url):
    if not registro_ids:
        return

    execution = Execution.objects.get(pk=execution_id)
    headless = getattr(settings, "AUTOMATION_HEADLESS", False)
    slow_mo = getattr(settings, "AUTOMATION_SLOW_MO", 500)
    wait_after_submit_ms = getattr(settings, "AUTOMATION_WAIT_AFTER_SUBMIT_MS", 2000)

    for registro_id in registro_ids:
        registro = Registro.objects.get(pk=registro_id)
        _marcar_registro_como_executando(registro=registro)
        resultado = _executar_registro(
            registro=registro,
            target_url=target_url,
            wait_after_submit_ms=wait_after_submit_ms,
            headless=headless,
            slow_mo=slow_mo,
        )
        _persistir_resultado(execution=execution, resultado=resultado)

    execution.status = "completed" if execution.erro_count == 0 else "error"
    execution.finalizado_em = timezone.now()
    execution.save(update_fields=["status", "finalizado_em"])


def _marcar_registro_como_executando(*, registro):
    registro.status = Registro.STATUS_EXECUTANDO
    registro.mensagem_erro = ""
    registro.executado_em = None
    registro.save(update_fields=["status", "mensagem_erro", "executado_em"])


def _executar_registro(*, registro, target_url, wait_after_submit_ms, headless, slow_mo):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()
            page.goto(target_url)
            page.fill("#nome", registro.nome)
            page.fill("#empresa", registro.empresa)
            page.fill("#email", registro.email)
            page.fill("#telefone", registro.telefone)
            page.click("button")
            page.wait_for_timeout(wait_after_submit_ms)
            browser.close()
    except Exception as exc:
        return {
            "registro_id": registro.id,
            "status": Registro.STATUS_ERRO,
            "mensagem_erro": str(exc),
            "executado_em": timezone.now(),
        }

    return {
        "registro_id": registro.id,
        "status": Registro.STATUS_EXECUTADO,
        "mensagem_erro": "",
        "executado_em": timezone.now(),
    }


def _persistir_resultado(*, execution, resultado):
    registro = Registro.objects.get(pk=resultado["registro_id"])
    registro.status = resultado["status"]
    registro.mensagem_erro = resultado["mensagem_erro"]
    registro.executado_em = resultado["executado_em"]
    registro.save(update_fields=["status", "mensagem_erro", "executado_em"])

    ResultadoExecucaoRegistro.objects.create(
        execution=execution,
        registro=registro,
        status="executado" if resultado["status"] == Registro.STATUS_EXECUTADO else "erro",
        mensagem_erro=resultado["mensagem_erro"],
        executado_em=resultado["executado_em"],
    )

    execution.linhas_processadas += 1
    if resultado["status"] == Registro.STATUS_EXECUTADO:
        execution.sucesso_count += 1
    else:
        execution.erro_count += 1
    execution.save(update_fields=["linhas_processadas", "sucesso_count", "erro_count"])
