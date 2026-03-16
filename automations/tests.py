from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from automations.models import Execution, ResultadoExecucaoRegistro
from automations.services import executar_automacoes
from registros.models import ImportacaoPlanilha, Registro


class _FakePage:
    def __init__(self, failing_email=None):
        self.failing_email = failing_email
        self.current_email = None

    def goto(self, target_url):
        self.target_url = target_url

    def fill(self, selector, value):
        if selector == "#email":
            self.current_email = value

    def click(self, selector):
        if self.current_email == self.failing_email:
            raise RuntimeError("Falha simulada")

    def wait_for_timeout(self, timeout_ms):
        self.timeout_ms = timeout_ms


class _FakeBrowserContext:
    def __init__(self, page):
        self.page = page

    def new_page(self):
        return self.page


class _FakeBrowser:
    def __init__(self, page):
        self.page = page

    def new_context(self, viewport):
        self.viewport = viewport
        return _FakeBrowserContext(self.page)

    def close(self):
        return None


class _FakeChromium:
    def __init__(self, page):
        self.page = page

    def launch(self, headless, slow_mo):
        self.headless = headless
        self.slow_mo = slow_mo
        return _FakeBrowser(self.page)


class _FakePlaywrightManager:
    def __init__(self, page):
        self.page = page
        self.chromium = _FakeChromium(page)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class AutomationsServiceTests(TestCase):
    def setUp(self):
        self.importacao = ImportacaoPlanilha.objects.create(
            nome_arquivo="base.xlsx",
            status=ImportacaoPlanilha.STATUS_CONCLUIDA,
            total_registros=2,
        )

    def test_execucao_atualiza_status_dos_registros_e_cria_resultados(self):
        page = _FakePage()
        Registro.objects.create(
            importacao=self.importacao,
            nome="Ana",
            empresa="Acme",
            email="ana@example.com",
            telefone="1111-1111",
        )
        Registro.objects.create(
            importacao=self.importacao,
            nome="Bruno",
            empresa="Beta",
            email="bruno@example.com",
            telefone="2222-2222",
        )

        with patch(
            "automations.services.sync_playwright",
            return_value=_FakePlaywrightManager(page),
        ):
            execution = executar_automacoes(target_url="http://testserver/form-teste/")

        self.assertEqual(execution.importacao, self.importacao)
        self.assertEqual(execution.status, "completed")
        self.assertEqual(execution.total_linhas, 2)
        self.assertEqual(execution.linhas_processadas, 2)
        self.assertEqual(execution.sucesso_count, 2)
        self.assertEqual(execution.erro_count, 0)
        self.assertEqual(Registro.objects.filter(status=Registro.STATUS_EXECUTADO).count(), 2)
        self.assertEqual(ResultadoExecucaoRegistro.objects.filter(execution=execution).count(), 2)

    def test_execucao_continua_quando_um_registro_falha(self):
        page = _FakePage(failing_email="erro@example.com")
        erro = Registro.objects.create(
            importacao=self.importacao,
            nome="Erro",
            empresa="Acme",
            email="erro@example.com",
            telefone="1111-1111",
        )
        sucesso = Registro.objects.create(
            importacao=self.importacao,
            nome="Sucesso",
            empresa="Beta",
            email="ok@example.com",
            telefone="2222-2222",
        )

        with patch(
            "automations.services.sync_playwright",
            return_value=_FakePlaywrightManager(page),
        ):
            execution = executar_automacoes(target_url="http://testserver/form-teste/")

        erro.refresh_from_db()
        sucesso.refresh_from_db()
        self.assertEqual(execution.status, "error")
        self.assertEqual(execution.sucesso_count, 1)
        self.assertEqual(execution.erro_count, 1)
        self.assertEqual(erro.status, Registro.STATUS_ERRO)
        self.assertIn("Falha simulada", erro.mensagem_erro)
        self.assertEqual(sucesso.status, Registro.STATUS_EXECUTADO)
        self.assertEqual(
            ResultadoExecucaoRegistro.objects.filter(execution=execution, status="erro").count(),
            1,
        )


class AutomationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.importacao = ImportacaoPlanilha.objects.create(
            nome_arquivo="base.xlsx",
            status=ImportacaoPlanilha.STATUS_CONCLUIDA,
            total_registros=2,
        )

    def test_get_nao_deve_executar_automacao(self):
        response = self.client.get(reverse("automations:executar"))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Execution.objects.count(), 0)

    def test_post_deve_redirecionar_para_listagem_com_execucao(self):
        execution = Execution.objects.create(
            importacao=self.importacao,
            status="running",
            total_linhas=2,
        )

        with patch(
            "automations.views.iniciar_automacoes_em_background",
            return_value=execution,
        ):
            response = self.client.post(reverse("automations:executar"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(f"execution_id={execution.id}", response.url)

    def test_endpoint_status_retorna_resumo_e_registros(self):
        registro = Registro.objects.create(
            importacao=self.importacao,
            nome="Ana",
            empresa="Acme",
            email="ana@example.com",
            telefone="1111-1111",
            status=Registro.STATUS_EXECUTADO,
        )
        execution = Execution.objects.create(
            importacao=self.importacao,
            status="running",
            total_linhas=1,
            linhas_processadas=0,
        )
        ResultadoExecucaoRegistro.objects.create(
            execution=execution,
            registro=registro,
            status="executado",
            mensagem_erro="",
            executado_em=registro.criado_em,
        )

        response = self.client.get(reverse("automations:status_execucao", args=[execution.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["execution"]["id"], execution.id)
        self.assertEqual(len(payload["registros"]), 1)
        self.assertEqual(payload["registros"][0]["id"], registro.id)

    def test_reprocessar_erros_redireciona_para_nova_execucao(self):
        erro = Registro.objects.create(
            importacao=self.importacao,
            nome="Erro",
            empresa="Acme",
            email="erro@example.com",
            telefone="1111-1111",
            status=Registro.STATUS_ERRO,
            mensagem_erro="falha antiga",
        )
        execution = Execution.objects.create(
            importacao=self.importacao,
            status="error",
            total_linhas=1,
            linhas_processadas=1,
            erro_count=1,
        )
        ResultadoExecucaoRegistro.objects.create(
            execution=execution,
            registro=erro,
            status="erro",
            mensagem_erro="Falha simulada",
            executado_em=erro.criado_em,
        )
        nova_execucao = Execution.objects.create(
            importacao=self.importacao,
            status="running",
            total_linhas=1,
        )

        with patch(
            "automations.views.iniciar_automacoes_em_background",
            return_value=nova_execucao,
        ):
            response = self.client.post(
                reverse("automations:reprocessar_erros", args=[execution.id])
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn(str(nova_execucao.id), response.url)
