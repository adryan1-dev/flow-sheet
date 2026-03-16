from django.db import models


class ImportacaoPlanilha(models.Model):
    STATUS_PROCESSANDO = "processando"
    STATUS_CONCLUIDA = "concluida"
    STATUS_ERRO = "erro"

    STATUS_CHOICES = [
        (STATUS_PROCESSANDO, "Processando"),
        (STATUS_CONCLUIDA, "Concluida"),
        (STATUS_ERRO, "Erro"),
    ]

    nome_arquivo = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PROCESSANDO,
    )
    total_registros = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_arquivo


class Registro(models.Model):
    STATUS_PENDENTE = "pendente"
    STATUS_EXECUTANDO = "executando"
    STATUS_EXECUTADO = "executado"
    STATUS_ERRO = "erro"

    STATUS_CHOICES = [
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_EXECUTANDO, "Executando"),
        (STATUS_EXECUTADO, "Executado"),
        (STATUS_ERRO, "Erro"),
    ]

    nome = models.CharField(max_length=200)
    empresa = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
    )
    mensagem_erro = models.TextField(blank=True)
    executado_em = models.DateTimeField(null=True, blank=True)
    importacao = models.ForeignKey(
        ImportacaoPlanilha,
        on_delete=models.CASCADE,
        related_name="registros",
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
