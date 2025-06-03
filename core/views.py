# core/views.py
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone # Para datas e horas com fuso horário
from .models import Systematic
import datetime

from .models import Systematic, SystematicPartRequired, ExecutionRecord

def calendario_view(request):
    """
    View que renderiza a página HTML onde o calendário será exibido.
    """

    
    today = timezone.now().date()
    sistematicas_ativas = Systematic.objects.filter(is_active=True)
    vencidas_count = 0
    for s in sistematicas_ativas:
        # Usando o método get_overall_status que já trata a lógica de "Atrasada"
        if s.get_overall_status().startswith("Atrasada"):
            vencidas_count += 1
            
    context = {
        'vencidas_count': vencidas_count,
    }
    return render(request, 'core/calendario_page.html', context)


def calendar_events_api(request):
    """
    API View para fornecer os eventos (sistemáticas) para o calendário.
    Espera parâmetros GET 'start' e 'end' no formato YYYY-MM-DD.
    """
    start_date_str = request.GET.get('start')
    end_date_str = request.GET.get('end')

    events = []

    if not start_date_str or not end_date_str:
        # Se as datas não forem fornecidas, pode retornar um erro ou um conjunto padrão.
        # Por enquanto, retornaremos uma lista vazia ou um erro.
        return JsonResponse({'error': 'Parâmetros start e end são obrigatórios.'}, status=400)

    try:
        # Converte as strings de data para objetos date do Python
        # Bibliotecas de calendário geralmente enviam no formato ISO (YYYY-MM-DD)
        start_date = datetime.datetime.strptime(start_date_str.split('T')[0], "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date_str.split('T')[0], "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({'error': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=400)

    sistematicas = Systematic.objects.filter(is_active=True)

    for sistematic in sistematicas:
        next_exec_date = sistematic.next_execution_date_calculated 

        if next_exec_date:
            # Verifica se a próxima data de execução está dentro do intervalo solicitado pelo calendário
            if start_date <= next_exec_date <= end_date:
                events.append({
                    'id': sistematic.id, # ID da sistemática
                    'title': f"{sistematic.name} ({sistematic.equipment.name})", # Título do evento no calendário
                    'start': next_exec_date.isoformat(), # Data de início no formato YYYY-MM-DD
                    # 'end': next_exec_date.isoformat(), # Se for um evento de dia único, start e end podem ser iguais
                    # 'url': reverse('core:systematic_detail', args=[sistematic.id]), # Exemplo se você tiver uma URL de detalhe
                    # 'color': '#007bff', # Você pode adicionar cores baseadas no tipo ou status
                    'description': sistematic.description or '',
                    'equipment': sistematic.equipment.name,
                    'line': sistematic.equipment.line.name,
                    'status': sistematic.get_overall_status(),
                    'detail_url': reverse('core:systematic_detail', args=[sistematic.id]), # <--- URL DE DETALHE
                })
    return JsonResponse(events, safe=False)

def systematic_detail_view (request, pk): #view para o detalhamento de sistematica
    systematic = get_object_or_404 (Systematic, pk = pk)
    parts_required = SystematicPartRequired.objects.filter(systematic = systematic)
    execution_history = ExecutionRecord.objects.filter(systematic = systematic).order_by('-scheduled_date', '-created_at')
    
    context ={
        'systematic': systematic,
        'parts_required': parts_required,
        'execution_history': execution_history,
        'vencidas_count': request.session.get('vencidas_count', 0)
        
    }
    
    today = timezone.now().date()
    sistematicas_ativas = Systematic.objects.filter(is_active=True)
    vencidas_count_atual = 0
    for s_obj in sistematicas_ativas:
        if s_obj.get_overall_status().startswith("Atrasada"):
            vencidas_count_atual += 1
    context['vencidas_count'] = vencidas_count_atual
    
    return render(request, 'core/systematic_detail.html', context)