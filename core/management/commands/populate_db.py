# core/management/commands/populate_db.py

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta, time
import random

# Importe seus modelos
from core.models import Line, Equipment, Part, TipoSystematic, Systematic, SystematicPartRequired, ExecutionRecord
from django.contrib.auth import get_user_model # Para pegar o modelo de User

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de simulação para o sistema de manutenção.'

    def add_arguments(self, parser):
        # Argumento opcional para limpar dados existentes antes de popular
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpa os dados existentes dos modelos antes de popular.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando a população do banco de dados...'))

        if options['clear']:
            self.clear_data()

        self.populate_data()

        self.stdout.write(self.style.SUCCESS('População do banco de dados concluída com sucesso!'))

    def clear_data(self):
        self.stdout.write(self.style.WARNING('Limpando dados existentes...'))
        # Ordem reversa da criação para respeitar as dependências
        ExecutionRecord.objects.all().delete()
        SystematicPartRequired.objects.all().delete()
        Systematic.objects.all().delete()
        Part.objects.all().delete()
        Equipment.objects.all().delete()
        TipoSystematic.objects.all().delete()
        Line.objects.all().delete()
        # User.objects.filter(is_superuser=False).delete() # Cuidado ao deletar usuários
        self.stdout.write(self.style.SUCCESS('Dados limpos.'))

    def populate_data(self):
        # Criar ou pegar um usuário para 'created_by' e 'executed_by'
        # Tenta pegar o primeiro superusuário ou cria um usuário simples se não houver.
        # Em um cenário real, você pode querer um usuário específico.
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_user(username='dev_user', password='password123', email='dev@example.com', is_staff=True)
            self.stdout.write(self.style.SUCCESS(f"Usuário de desenvolvimento '{user.username}' criado."))


        # 1. Criar Linhas
        self.stdout.write("Criando Linhas...")
        lines_data = ["Linha Convertidora 01", "Linha Rebobinadeira Alpha", "Linha Embalagem Primária"]
        lines = []
        for name in lines_data:
            line, created = Line.objects.get_or_create(name=name)
            lines.append(line)
            if created: self.stdout.write(f"  Linha '{line.name}' criada.")

        # 2. Criar Tipos de Sistemática
        self.stdout.write("Criando Tipos de Sistemática...")
        tipos_data = [
            ("Manutenção Preventiva", "Manutenção realizada para prevenir falhas."),
            ("Lubrificação", "Aplicação de lubrificantes em pontos específicos."),
            ("Ajuste de Parâmetro", "Calibração ou ajuste de configurações da máquina."),
            ("Inspeção Visual", "Verificação visual de componentes."),
            ("Medição de Desgaste", "Medição para acompanhar o desgaste de peças.")
        ]
        tipos_sistematic = []
        for nome, desc in tipos_data:
            tipo, created = TipoSystematic.objects.get_or_create(nome=nome, defaults={'descricao': desc})
            tipos_sistematic.append(tipo)
            if created: self.stdout.write(f"  Tipo '{tipo.nome}' criado.")
        
        # 3. Criar Equipamentos
        self.stdout.write("Criando Equipamentos...")
        equipments_data = [
            ("Cabeçote de Corte A", lines[0]), ("Sistema de Relevo X", lines[0]),
            ("Motor Principal Rebobinadeira", lines[1]), ("Painel Elétrico Rebob.", lines[1]),
            ("Esteira de Saída Emb.", lines[2]), ("Datador Emb.", lines[2])
        ]
        equipments = []
        for name, line_obj in equipments_data:
            equip, created = Equipment.objects.get_or_create(name=name, line=line_obj)
            equipments.append(equip)
            if created: self.stdout.write(f"  Equipamento '{equip.name}' criado na linha '{line_obj.name}'.")

        # 4. Criar Peças
        self.stdout.write("Criando Peças...")
        parts_data = [
            ("Rolamento 6205ZZ", "SAP-ROL-001"), ("Lâmina de Corte Circular 150mm", "SAP-LAM-002"),
            ("Óleo Lubrificante ISO VG 68", "SAP-OLE-003"), ("Correia Trapezoidal XPZ 987", "SAP-COR-004"),
            ("Filtro de Ar Pneu.", "SAP-FIL-005"), ("Sensor Indutivo M12", "SAP-SEN-006")
        ]
        parts = []
        for name, sap_code in parts_data:
            part, created = Part.objects.get_or_create(sap_code=sap_code, defaults={'name': name})
            parts.append(part)
            if created: self.stdout.write(f"  Peça '{part.name}' criada.")

        # 5. Criar Sistemáticas e Registros de Execução
        self.stdout.write("Criando Sistemáticas e alguns Registros de Execução...")
        today = timezone.now().date()

        systematics_to_create = [
            {
                'name': "Verificação Semanal Alinhamento Cabeçote A", 'tipo': tipos_sistematic[3], # Inspeção Visual
                'equipment': equipments[0], 'range_days': 7, 'created_by': user,
                'last_exec_offset_days': -random.randint(5, 9), # Última execução entre 5-9 dias atrás
                'parts_required': [(parts[1], 1.0)] # Lâmina, 1 unidade
            },
            {
                'name': "Lubrificação Mensal Motor Rebobinadeira", 'tipo': tipos_sistematic[1], # Lubrificação
                'equipment': equipments[2], 'range_days': 30, 'created_by': user,
                'last_exec_offset_days': -random.randint(25, 35), # Última execução entre 25-35 dias atrás
                'parts_required': [(parts[2], 0.5)] # Óleo
            },
            {
                'name': "Inspeção Quinzenal Filtro de Ar Datador", 'tipo': tipos_sistematic[3], # Inspeção Visual
                'equipment': equipments[5], 'range_days': 15, 'created_by': user,
                'last_exec_offset_days': -random.randint(10, 20)
            },
            {
                'name': "Ajuste Semestral Sensor Indutivo Esteira", 'tipo': tipos_sistematic[2], # Ajuste
                'equipment': equipments[4], 'range_days': 180, 'created_by': user,
                'last_exec_offset_days': -random.randint(170,190),
                'parts_required': [(parts[5], 1.0)]
            },
            {
                'name': "Preventiva Bimestral Painel Elétrico Rebob.", 'tipo': tipos_sistematic[0], # Preventiva
                'equipment': equipments[3], 'range_days': 60, 'created_by': user,
                'last_exec_offset_days': None # Nunca executada, para testar o "Requer 1º Agendamento"
            },
             {
                'name': "Medição de Vibração Motor Rebobinadeira (Trimestral)", 'tipo': tipos_sistematic[4], # Medição
                'equipment': equipments[2], 'range_days': 90, 'created_by': user,
                'last_exec_offset_days': -random.randint(1,5), # Recente, para estar "Em Dia"
            },
        ]

        for sys_data in systematics_to_create:
            # Cria a Sistemática
            systematic_obj, created = Systematic.objects.get_or_create(
                name=sys_data['name'],
                defaults={
                    'tipo_systematic': sys_data['tipo'],
                    'equipment': sys_data['equipment'],
                    'range_days': sys_data['range_days'],
                    'description': f"Procedimento padrão para {sys_data['name']}.",
                    'created_by': sys_data['created_by'],
                    'is_active': True
                }
            )
            if created: self.stdout.write(f"  Sistemática '{systematic_obj.name}' criada.")

            # Adiciona peças necessárias, se houver
            if 'parts_required' in sys_data:
                for part_obj, qty in sys_data['parts_required']:
                    SystematicPartRequired.objects.get_or_create(
                        systematic=systematic_obj,
                        part=part_obj,
                        defaults={'quantity_required': qty}
                    )

            # Cria um Registro de Execução passado, se aplicável
            if sys_data.get('last_exec_offset_days') is not None:
                exec_date = today + timedelta(days=sys_data['last_exec_offset_days'])
                ExecutionRecord.objects.get_or_create(
                    systematic=systematic_obj,
                    scheduled_date=exec_date, # Data agendada igual à de execução para simplificar
                    defaults={
                        'execution_start_date': timezone.make_aware(datetime.combine(exec_date, time(9,0))),
                        'execution_end_date': timezone.make_aware(datetime.combine(exec_date, time(10,0))), # Ajustei para 1 hora de duração como exemplo
                        'executed_by': user,
                        'status': random.choice(['CONCLUIDA', 'CONCLUIDA_ATRASO']),
                        'observations': 'Execução de simulação via script.'
                        
                    }
                )
                if created: self.stdout.write(f"    -> Registro de execução passado criado para '{systematic_obj.name}' em {exec_date}.")
            elif created:
                 self.stdout.write(f"    -> Sem execução passada para '{systematic_obj.name}'. Será 'Requer 1º Agendamento'.")


        # Adicionar alguns ExecutionRecords PENDENTES para o futuro próximo
        self.stdout.write("Agendando algumas execuções futuras...")
        future_systematics = Systematic.objects.filter(is_active=True).order_by('?')[:2] # Pega 2 aleatórias
        for systematic_obj in future_systematics:
            # Verifica se já tem alguma pendente para não duplicar agendamento simples
            if not ExecutionRecord.objects.filter(systematic=systematic_obj, status='PENDENTE').exists():
                # Calcula a próxima data com base na lógica do modelo, se possível, ou agenda genericamente
                next_date_calc = systematic_obj.next_execution_date_calculated
                scheduled_future_date = next_date_calc if next_date_calc else today + timedelta(days=random.randint(1, 10))

                ExecutionRecord.objects.get_or_create(
                    systematic=systematic_obj,
                    scheduled_date=scheduled_future_date,
                    status='PENDENTE', # Importante para o get_overall_status
                    defaults={'executed_by': None, 'observations': 'Agendado via script de simulação.'}
                )
                self.stdout.write(f"  -> Agendamento PENDENTE criado para '{systematic_obj.name}' em {scheduled_future_date}.")