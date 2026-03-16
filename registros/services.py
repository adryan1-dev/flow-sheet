import openpyxl

from .models import ImportacaoPlanilha, Registro


def importar_planilha(arquivo):
    importacao = ImportacaoPlanilha.objects.create(
        nome_arquivo=arquivo.name,
        status=ImportacaoPlanilha.STATUS_PROCESSANDO,
        total_registros=0,
    )

    workbook = openpyxl.load_workbook(arquivo)
    sheet = workbook.active

    registros = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        nome, empresa, email, telefone = row

        registros.append(
            Registro(
                importacao=importacao,
                nome=nome,
                empresa=empresa,
                email=email,
                telefone=telefone,
                status=Registro.STATUS_PENDENTE,
            )
        )

    Registro.objects.bulk_create(registros)

    importacao.total_registros = len(registros)
    importacao.status = ImportacaoPlanilha.STATUS_CONCLUIDA
    importacao.save(update_fields=["total_registros", "status"])

    return importacao
