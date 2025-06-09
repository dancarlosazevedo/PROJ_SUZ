# app_manutencao/models.py

from django.db import models
from django.conf import settings # Para ForeignKey para User
from django.utils import timezone
from datetime import timedelta
from simple_history.models import HistoricalRecords

# --------------------
# Modelos Principais
# --------------------

class Line(models.Model):
    """
    Linha de produção
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome da Linha")
    # Futuramente: codigo_identificacao, descricao, localizacao, ativa

    class Meta:
        verbose_name = "Linha de Produção"
        verbose_name_plural = "Linhas de Produção"
        ordering = ['name']

    def __str__(self):
        return self.name

class Equipment(models.Model):
    """
    Equipamento onde será cadastrado a sistemática
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome do Equipamento")
    line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name='equipamentos', verbose_name="Linha de Produção")
    # Futuramente: tag_identificacao, fabricante, modelo, numero_serie, data_instalacao, criticidade

    class Meta:
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"
        ordering = ['line__name', 'name']

    def __str__(self):
        return f"{self.name} (Linha: {self.line.name})"

class Part(models.Model):
    """
    Item necessário para a sistemática (Peça de reposição/consumível)
    """
    name = models.CharField(max_length=100, verbose_name="Nome da Peça")
    sap_code = models.CharField(max_length=50, unique=True, verbose_name="Código SAP")
    # Futuramente: descricao, fabricante, modelo_peca, unidade_medida, quantidade_em_estoque, estoque_minimo

    class Meta:
        verbose_name = "Peça"
        verbose_name_plural = "Peças"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sap_code})"

class TipoSystematic(models.Model):
    """
    Categoriza os diferentes tipos de intervenções (Sistemáticas).
    Ex: Manutenção Preventiva, Ajuste de Parâmetro, Medição, Lubrificação.
    """
    nome = models.CharField(max_length=100, unique=True, help_text="Ex: Manutenção Preventiva", verbose_name="Nome do Tipo")
    descricao = models.TextField(blank=True, null=True, help_text="Descrição detalhada do que este tipo de sistemática envolve.", verbose_name="Descrição")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Tipo de Sistemática"
        verbose_name_plural = "Tipos de Sistemáticas"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Systematic(models.Model):
    """
    Sistemática de manutenção, ajuste ou medição
    """
    tipo_systematic = models.ForeignKey(
        TipoSystematic,
        on_delete=models.PROTECT, # Evita excluir um tipo se houver sistemáticas associadas
        related_name='systematics',
        verbose_name="Tipo de Sistemática"
    )
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome da Sistemática") # ex: "Verificação Semanal do Cabeçote"
    description = models.TextField(blank=True, null=True, verbose_name="Descrição do Procedimento") # "O que vai ser feito"
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='systematics', verbose_name="Equipamento")
    range_days = models.PositiveIntegerField(default=0, help_text="Intervalo em dias para a próxima execução. 0 ou Nulo se não aplicável.", verbose_name="Frequência (dias)", null=True, blank=True)
    time_estimated_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Tempo estimado em minutos para execução", verbose_name="Tempo Estimado (min)")
    safety_instructions = models.TextField(blank=True, null=True, verbose_name="Instruções de Segurança")
    # needs_equipment_stop = models.BooleanField(default=False, verbose_name="Requer Parada do Equipamento?")
    is_active = models.BooleanField(default=True, verbose_name="Sistemática Ativa?")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='systematics_criadas',
        verbose_name="Criado por"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Sistemática"
        verbose_name_plural = "Sistemáticas"
        ordering = ['equipment__line__name', 'equipment__name', 'name']

    def __str__(self):
        return f"{self.name} ({self.tipo_systematic.nome if self.tipo_systematic else 'N/A'}) - {self.equipment.name}"

    @property
    def last_completed_execution_record(self):
        """Retorna o último ExecutionRecord concluído para esta sistemática, ou None."""
        return self.execution_records.filter(
            status__in=['CONCLUIDA', 'CONCLUIDA_ATRASO']
        ).order_by('-execution_end_date', '-scheduled_date').first() # Prioriza execution_end_date

    @property
    def last_execution_date_display(self):
        """Retorna a data de término (ou agendada) da última execução concluída, ou None."""
        last_exec = self.last_completed_execution_record
        if last_exec:
            return last_exec.execution_end_date.date() if last_exec.execution_end_date else last_exec.scheduled_date
        return None

    @property
    def next_execution_date_calculated(self):
        """Calcula a próxima data de execução."""
        if self.range_days is None or self.range_days <= 0:
            return None

        last_exec_date = self.last_execution_date_display
        if last_exec_date:
            return last_exec_date + timedelta(days=self.range_days)
        # Se nunca foi executada E range_days > 0, a próxima pode ser baseada na data de criação.
        # Mas pode ser melhor forçar o primeiro agendamento via ExecutionRecord.
        # return self.created_at.date() + timedelta(days=self.range_days) # Opção
        return None # Indica que a primeira execução precisa ser agendada

    def get_overall_status(self):
        """Retorna um status geral para a sistemática (Ex: 'Em Dia', 'Pendente', 'Atrasada')."""
        if not self.is_active:
            return "Inativa"

        # Verifica se existe algum registro de execução em aberto (Pendente ou Em Andamento)
        open_executions = self.execution_records.filter(status__in=['PENDENTE', 'EM_ANDAMENTO']).order_by('scheduled_date').first()
        if open_executions:
            if open_executions.scheduled_date <= timezone.now().date():
                 return f"Agendada (Vence {open_executions.scheduled_date.strftime('%d/%m')})"
            return f"Agendada ({open_executions.scheduled_date.strftime('%d/%m')})"

        next_date = self.next_execution_date_calculated
        if not next_date:
            if self.range_days and self.range_days > 0:
                return "Requer 1º Agendamento"
            else:
                return "Não Recorrente" # Ou "Verificar Config" se range_days for 0 mas deveria ser recorrente

        today = timezone.now().date()
        if next_date < today:
            return f"Atrasada (Devia ser {next_date.strftime('%d/%m')})"
        elif next_date == today:
            return "Pendente Hoje"
        else:
            if (next_date - today).days <= 7:
                return f"Próxima ({next_date.strftime('%d/%m')}, em {(next_date - today).days}d)"
            return f"Em Dia (Próx. {next_date.strftime('%d/%m')})"

class SystematicPartRequired(models.Model):
    """
    Peças e suas quantidades necessárias para uma Sistemática específica.
    """
    systematic = models.ForeignKey(Systematic, on_delete=models.CASCADE, related_name="required_parts_info", verbose_name="Sistemática")
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name="used_in_systematics_info", verbose_name="Peça") # PROTECT para não deletar peça se estiver em uso
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2, default=1.0, verbose_name="Quantidade Necessária")
    observation = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observação")

    class Meta:
        unique_together = ('systematic', 'part') # Garante que uma peça só apareça uma vez por sistemática
        verbose_name = "Peça Necessária para Sistemática"
        verbose_name_plural = "Peças Necessárias para Sistemáticas"
        ordering = ['systematic', 'part__name']

    def __str__(self):
        return f"{self.quantity_required} x {self.part.name} para {self.systematic.name}"

class ExecutionRecord(models.Model):
    """
    Registro de cada execução de uma Sistemática.
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDA', 'Concluída'),
        ('CONCLUIDA_ATRASO', 'Concluída com Atraso'),
        ('NAO_REALIZADA', 'Não Realizada'), # Ex: pulou esta vez
        ('CANCELADA', 'Cancelada'), # Ex: sistemática desativada ou erro no agendamento
    ]

    systematic = models.ForeignKey(Systematic, on_delete=models.CASCADE, related_name="execution_records", verbose_name="Sistemática")
    scheduled_date = models.DateField(help_text="Data em que a execução está/estava prevista", verbose_name="Data Agendada")
    execution_start_date = models.DateTimeField(null=True, blank=True, help_text="Quando a execução efetivamente começou", verbose_name="Início da Execução")
    execution_end_date = models.DateTimeField(null=True, blank=True, help_text="Quando a execução efetivamente terminou", verbose_name="Fim da Execução")

    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="systematics_executed",
        verbose_name="Executado por"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE', verbose_name="Status")
    observations = models.TextField(blank=True, null=True, help_text="Anotações, problemas encontrados, medições realizadas, etc.", verbose_name="Observações da Execução")
    # Futuramente: real_execution_time_minutes (calculado ou inputado), custo_adicional

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação do Registro")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização do Registro")

    class Meta:
        verbose_name = "Registro de Execução"
        verbose_name_plural = "Registros de Execução"
        ordering = ['-scheduled_date', '-created_at'] # Mais recentes primeiro

    def __str__(self):
        return f"Exec. {self.systematic.name} em {self.scheduled_date.strftime('%d/%m/%Y')} - {self.get_status_display()}"

    def clean(self):
        # Validação: Data de término não pode ser anterior à data de início
        if self.execution_start_date and self.execution_end_date:
            if self.execution_end_date < self.execution_start_date:
                from django.core.exceptions import ValidationError
                raise ValidationError({'execution_end_date': 'A data de término não pode ser anterior à data de início.'})
            
            
        def save(self, *args, **kwargs):
            super().save(*args, **kwargs)

            # ⚙️ Agendamento automático da próxima execução se esta foi concluída
            if self.status in ['CONCLUIDA', 'CONCLUIDA_ATRASO']:
                s = self.systematic

                # Se a sistemática tem intervalo definido
                if s.range_days and s.range_days > 0:
                    proxima_data = self.scheduled_date + timedelta(days=s.range_days)

                    # Verifica se já existe execução programada nessa data
                    existe = s.execution_records.filter(scheduled_date=proxima_data).exists()

                    if not existe:
                        ExecutionRecord.objects.create(
                            systematic=s,
                            scheduled_date=proxima_data,
                            status='PENDENTE'
                        )

 