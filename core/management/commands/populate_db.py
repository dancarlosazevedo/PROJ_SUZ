# core/management/commands/populate_db.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, time # Certifique-se que 'time' está importado
import random

from core.models import Line, Equipment, Part, TipoSystematic, Systematic, SystematicPartRequired, ExecutionRecord
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de simulação para o sistema de manutenção, incluindo novas linhas e múltiplas sistemáticas por linha.'

    def add_arguments(self, parser):
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
        ExecutionRecord.objects.all().delete()
        SystematicPartRequired.objects.all().delete()
        Systematic.objects.all().delete()
        Part.objects.all().delete()
        Equipment.objects.all().delete()
        TipoSystematic.objects.all().delete()
        Line.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Dados limpos.'))

    def populate_data(self):
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_user(username='dev_user', password='password123', email='dev@example.com', is_staff=True)
            self.stdout.write(self.style.SUCCESS(f"Usuário de desenvolvimento '{user.username}' criado."))

        # 1. Criar Linhas (ATUALIZADO)
        self.stdout.write("Criando Linhas...")
        lines_data = [
            "Linha 15", "Linha 14", "Linha 13", "Linha 12", "Linha 08", "Linha 07", 
            "Linha 06", "Linha 05", "P732", "Amica", "Bretting", "Chen Rong"
        ]
        lines = []
        for name in lines_data:
            line, created = Line.objects.get_or_create(name=name)
            lines.append(line)
            if created: self.stdout.write(f"  Linha '{line.name}' criada.")

        # 2. Criar Tipos de Sistemática (Mantido)
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
        
        if not tipos_sistematic: # Garante que temos tipos para usar
            self.stdout.write(self.style.ERROR("Nenhum Tipo de Sistemática encontrado ou criado. Saindo."))
            return

        # 3. Criar Equipamentos (ATUALIZADO - 2 por linha)
        self.stdout.write("Criando Equipamentos...")
        equipments_by_line = {} # Para fácil acesso depois
        for line_obj in lines:
            equipments_by_line[line_obj.id] = []
            for i in range(1, 3): # Criar 2 equipamentos por linha
                equip_name = f"Equipamento {chr(64+i)} - {line_obj.name}" # Equipamento A - Linha X, Equipamento B - Linha X
                equip, created = Equipment.objects.get_or_create(name=equip_name, defaults={'line': line_obj})
                equipments_by_line[line_obj.id].append(equip)
                if created: self.stdout.write(f"  Equipamento '{equip.name}' criado.")
        
        # 4. Criar Peças (Mantido)
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

        # 5. Criar Sistemáticas e Registros de Execução (ATUALIZADO - Pelo menos 5 por linha)
        self.stdout.write("Criando Sistemáticas e alguns Registros de Execução...")
        today = timezone.now().date()
        sistematic_count_total = 0

        for line_obj in lines:
            line_equipments = equipments_by_line.get(line_obj.id, [])
            if not line_equipments:
                self.stdout.write(self.style.WARNING(f"  Nenhum equipamento encontrado para a Linha '{line_obj.name}'. Pulando sistemáticas para esta linha."))
                continue

            self.stdout.write(f"  Criando sistemáticas para a Linha '{line_obj.name}'...")
            for i in range(5): # Criar 5 sistemáticas por linha
                chosen_equipment = random.choice(line_equipments) # Escolhe um equipamento aleatório da linha
                chosen_tipo_sistematic = random.choice(tipos_sistematic)
                systematic_name = f"Sistemática {i+1} ({chosen_tipo_sistematic.nome}) - {chosen_equipment.name}"
                
                range_days_options = [7, 15, 30, 60, 90, 180]
                chosen_range_days = random.choice(range_days_options)

                systematic_obj, created = Systematic.objects.get_or_create(
                    name=systematic_name,
                    equipment=chosen_equipment, # Garante que o nome + equipamento seja único
                    defaults={
                        'tipo_systematic': chosen_tipo_sistematic,
                        'range_days': chosen_range_days,
                        'description': f"Procedimento de simulação para {systematic_name}.",
                        'created_by': user,
                        'is_active': True,
                        'time_estimated_minutes': random.randint(15, 120)
                    }
                )
                sistematic_count_total +=1

                if created: 
                    self.stdout.write(f"    Sistemática '{systematic_obj.name}' criada.")

                    # Adiciona peças necessárias aleatoriamente (0 a 2 peças)
                    if parts and random.choice([True, False]): # 50% de chance de adicionar peças
                        num_parts_to_add = random.randint(0, min(2, len(parts)))
                        selected_parts = random.sample(parts, num_parts_to_add)
                        for part_obj in selected_parts:
                            SystematicPartRequired.objects.get_or_create(
                                systematic=systematic_obj,
                                part=part_obj,
                                defaults={'quantity_required': float(random.randint(1,5))}
                            )

                    # Cria um Registro de Execução passado para ~70% das novas sistemáticas
                    if random.random() < 0.7: 
                        last_exec_offset = -random.randint(1, chosen_range_days + 15) # Até 15 dias depois do "vencimento"
                        exec_date = today + timedelta(days=last_exec_offset)
                        
                        ExecutionRecord.objects.get_or_create(
                            systematic=systematic_obj,
                            scheduled_date=exec_date, 
                            status=random.choice(['CONCLUIDA', 'CONCLUIDA_ATRASO']),
                            defaults={
                                'execution_start_date': timezone.make_aware(datetime.combine(exec_date, time(9,0))),
                                'execution_end_date': timezone.make_aware(datetime.combine(exec_date, time(random.randint(9,10),random.randint(0,59)))),
                                'executed_by': user,
                                'observations': 'Execução de simulação via script (passado).'
                            }
                        )
                        self.stdout.write(f"      -> Registro de execução passado criado para '{systematic_obj.name}' em {exec_date}.")
                    else:
                         self.stdout.write(f"      -> Sem execução passada para '{systematic_obj.name}'. Próxima data será baseada na criação ou agendamento manual.")

        self.stdout.write(f"{sistematic_count_total} sistemáticas no total processadas ou criadas.")
        
        # Adicionar alguns ExecutionRecords PENDENTES para o futuro próximo (mantido)
        self.stdout.write("Agendando algumas execuções futuras...")
        # Pega até 5 sistemáticas ativas aleatórias que não tenham execuções pendentes
        active_systematics_for_future = Systematic.objects.filter(is_active=True).exclude(execution_records__status='PENDENTE').order_by('?')[:5]
        
        for systematic_obj in active_systematics_for_future:
            next_date_calc = systematic_obj.next_execution_date_calculated
            # Se next_execution_date_calculated for None (nunca executada e com range_days),
            # agende para daqui a alguns dias a partir de hoje.
            # Se tiver uma data calculada, use-a.
            if next_date_calc:
                 scheduled_future_date = next_date_calc
            else: # Nunca executada ou sem range_days. Agendar genericamente.
                # Se range_days > 0, implica que deveria ter uma primeira execução.
                # Se não, é one-shot, não deveria ter PENDENTE automaticamente.
                if systematic_obj.range_days and systematic_obj.range_days > 0:
                    scheduled_future_date = today + timedelta(days=random.randint(1, systematic_obj.range_days // 2 or 7))
                else:
                    continue # Não agenda PENDENTE para sistemáticas sem recorrência e nunca executadas


            # Garante que a data agendada não seja no passado se calculada.
            if scheduled_future_date < today:
                # Se a data calculada for no passado (sistemática atrasada),
                # não criamos um PENDENTE para essa data, pois já está atrasada.
                # O status dela já reflete isso.
                # Poderíamos criar um PENDENTE para HOJE se estiver muito atrasada.
                # Mas para simplificar, vamos pular o agendamento PENDENTE se a data calculada for passada.
                self.stdout.write(f"  -> Próxima data calculada para '{systematic_obj.name}' ({scheduled_future_date}) está no passado. Não será criado PENDENTE automático.")
                continue


            ExecutionRecord.objects.get_or_create(
                systematic=systematic_obj,
                scheduled_date=scheduled_future_date,
                status='PENDENTE', 
                defaults={'executed_by': None, 'observations': 'Agendado via script de simulação.'}
            )
            self.stdout.write(f"  -> Agendamento PENDENTE criado para '{systematic_obj.name}' em {scheduled_future_date}.")