from io import BytesIO

from django.test import Client
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from registros.models import ImportacaoPlanilha, Registro
from registros.services import importar_planilha


class ImportarPlanilhaTests(TestCase):
    def test_importacao_cria_lote_novo_sem_apagar_historico(self):
        importacao_antiga = ImportacaoPlanilha.objects.create(
            nome_arquivo="antiga.xlsx",
            status=ImportacaoPlanilha.STATUS_CONCLUIDA,
            total_registros=1,
        )
        Registro.objects.create(
            importacao=importacao_antiga,
            nome="Antigo",
            empresa="Legacy",
            email="legacy@example.com",
            telefone="0000-0000",
            status=Registro.STATUS_ERRO,
            mensagem_erro="erro antigo",
        )

        arquivo = BytesIO()
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["nome", "empresa", "email", "telefone"])
        sheet.append(["Ana", "Acme", "ana@example.com", "1111-1111"])
        workbook.save(arquivo)
        arquivo.seek(0)
        arquivo.name = "nova.xlsx"

        importacao = importar_planilha(arquivo)

        self.assertEqual(ImportacaoPlanilha.objects.count(), 2)
        self.assertEqual(Registro.objects.count(), 2)
        self.assertEqual(importacao.nome_arquivo, "nova.xlsx")
        self.assertEqual(importacao.status, ImportacaoPlanilha.STATUS_CONCLUIDA)
        self.assertEqual(importacao.total_registros, 1)
        registro = Registro.objects.get(importacao=importacao)
        self.assertEqual(registro.nome, "Ana")
        self.assertEqual(registro.status, Registro.STATUS_PENDENTE)
        self.assertEqual(registro.mensagem_erro, "")
        self.assertEqual(registro.importacao, importacao)


class EditarRegistroTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.importacao = ImportacaoPlanilha.objects.create(
            nome_arquivo="base.xlsx",
            status=ImportacaoPlanilha.STATUS_CONCLUIDA,
            total_registros=1,
        )

    def test_edicao_atualiza_dados_e_redefine_status_para_pendente(self):
        registro = Registro.objects.create(
            importacao=self.importacao,
            nome="Ana",
            empresa="Acme",
            email="ana@example.com",
            telefone="1111-1111",
            status=Registro.STATUS_ERRO,
            mensagem_erro="Erro anterior",
        )

        response = self.client.post(
            reverse("editar_registro", args=[registro.id]),
            {
                "nome": "Ana Maria",
                "empresa": "Nova Empresa",
                "email": "ana.maria@example.com",
                "telefone": "11988887777",
            },
        )

        self.assertEqual(response.status_code, 302)
        registro.refresh_from_db()
        self.assertEqual(registro.nome, "Ana Maria")
        self.assertEqual(registro.empresa, "Nova Empresa")
        self.assertEqual(registro.email, "ana.maria@example.com")
        self.assertEqual(registro.telefone, "11988887777")
        self.assertEqual(registro.status, Registro.STATUS_PENDENTE)
        self.assertEqual(registro.mensagem_erro, "")
        self.assertIsNone(registro.executado_em)
