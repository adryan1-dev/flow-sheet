from django.contrib.auth.models import User
from django.db import models


class Execution(models.Model):
    importacao = models.ForeignKey(
        "registros.ImportacaoPlanilha",
        on_delete=models.SET_NULL,
        related_name="executions",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="executions",
        null=True,
        blank=True,
    )

    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("running", "Executando"),
        ("completed", "Concluida"),
        ("error", "Erro"),
    ]

    arquivo_planilha = models.FileField(upload_to="uploads/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    target_url = models.URLField(blank=True)
    total_linhas = models.IntegerField(default=0)
    linhas_processadas = models.IntegerField(default=0)
    sucesso_count = models.IntegerField(default=0)
    erro_count = models.IntegerField(default=0)
    mensagem_erro = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    finalizado_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Execution {self.id} - {self.status}"


class ResultadoExecucaoRegistro(models.Model):
    STATUS_CHOICES = [
        ("executado", "Executado"),
        ("erro", "Erro"),
    ]

    execution = models.ForeignKey(
        Execution,
        on_delete=models.CASCADE,
        related_name="resultados",
    )
    registro = models.ForeignKey(
        "registros.Registro",
        on_delete=models.CASCADE,
        related_name="resultados_execucao",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    mensagem_erro = models.TextField(blank=True)
    executado_em = models.DateTimeField()

    def __str__(self):
        return f"Execucao {self.execution_id} - Registro {self.registro_id}"
