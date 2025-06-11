# core/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone # Para datas e horas com fuso horário
from .models import Systematic, SystematicPartRequired, Equipment, Line, Part
from .forms import SystematicForm, ExecutionRecordForm, SystematicPartFormSet, PartForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime
from django.contrib.auth.decorators import user_passes_test, login_required
from .utils import group_required
from .models import Systematic, SystematicPartRequired, ExecutionRecord
from django.views.decorators.http import require_POST
from django.contrib.auth.views import LoginView


from django.http import HttpResponseForbidden

def group_required(*group_names):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.groups.filter(name__in=group_names).exists():
                return HttpResponseForbidden("Acesso restrito.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    
def calendario_view(request):
    """
    View que renderiza a página HTML onde o calendário será exibido.
    """

    linhas_todas = Line.objects.all()
    today = timezone.now().date()
    sistematicas_ativas = Systematic.objects.filter(is_active=True)
    vencidas_count = 0
    for s in sistematicas_ativas:
        # Usando o método get_overall_status que já trata a lógica de "Atrasada"
        if s.get_overall_status().startswith("Atrasada"):
            vencidas_count += 1
            
    context = {
        'vencidas_count': vencidas_count,
        'linhas_todas': linhas_todas,
    }
    return render(request, 'core/calendario_page.html', context)



def calendar_events_api(request):
    linha_id = request.GET.get('linha_id')
    eventos = ExecutionRecord.objects.select_related('systematic', 'systematic__equipment', 'systematic__equipment__line')

    if linha_id:
        eventos = eventos.filter(systematic__equipment__line_id=linha_id)
        
    start_date_str = request.GET.get('start')
    end_date_str = request.GET.get('end')
    events = []

    if not start_date_str or not end_date_str:
        return JsonResponse({'error': 'Parâmetros start e end são obrigatórios.'}, status=400)

    try:
        start_date = datetime.datetime.strptime(start_date_str.split('T')[0], "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date_str.split('T')[0], "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({'error': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=400)

    sistematicas = Systematic.objects.filter(is_active=True)
    
    if linha_id:
     sistematicas = sistematicas.filter(equipment__line_id=linha_id)

    color_map = {
        'Atrasada': '#dc3545',                # vermelho
        'Pendente': '#ffc107',                # amarelo
        'Pendente Hoje': '#ffc107',           # amarelo
        'Próxima': '#28a745',                 # verde
        'Em Dia': '#198754',                  # verde escuro
        'Agendada': '#0d6efd',                # azul
        'Inativa': '#6c757d',                 # cinza
        'Requer': '#17a2b8',                  # azul claro
    }

    for sistematic in sistematicas:
        next_exec_date = sistematic.next_execution_date_calculated

        if next_exec_date and start_date <= next_exec_date <= end_date:
            status = sistematic.get_overall_status()
            cor_base = '#adb5bd'  # cinza claro padrão

            for chave, cor in color_map.items():
                if status.startswith(chave):
                    cor_base = cor
                    break

            events.append({
                'id': sistematic.id,
                'title': f"{sistematic.name} ({sistematic.equipment.name})",
                'start': next_exec_date.isoformat(),
                'description': sistematic.description or '',
                'equipment': sistematic.equipment.name,
                'line': sistematic.equipment.line.name,
                'status': status,
                'detail_url': reverse('core:systematic_detail', args=[sistematic.id]),
                'backgroundColor': cor_base,
                'borderColor': cor_base,
                'textColor': '#fff'
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

@group_required('Administrador', 'Técnico')
def systematic_edit_view(request, pk):
    systematic = get_object_or_404(Systematic, pk=pk)

    if request.method == 'POST':
        form = SystematicForm(request.POST, instance=systematic)
        formset = SystematicPartFormSet(request.POST, instance=systematic)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            messages.success(request, 'Sistemática atualizada com sucesso!')
            return redirect('core:systematic_detail', pk=pk)
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = SystematicForm(instance=systematic)
        formset = SystematicPartFormSet(instance=systematic)

    return render(request, 'core/systematic_form.html', {
        'form': form,
        'formset': formset,
        'systematic': systematic
    })


@group_required('Administrador', 'Técnico')
def register_execution_view(request, pk):
    systematic = get_object_or_404(Systematic, pk=pk)

    if request.method == 'POST':
        form = ExecutionRecordForm(request.POST)
        if form.is_valid():
            exec_record = form.save(commit=False)
            exec_record.systematic = systematic
            exec_record.executed_by = request.user
            exec_record.save()
            return redirect('core:systematic_detail', pk=pk)
    else:
        form = ExecutionRecordForm(initial={
            'scheduled_date': timezone.now().date(),
            'status': 'CONCLUIDA',
            'execution_start_date': timezone.now(),
            'execution_end_date': timezone.now(),
        })

    return render(request, 'core/execution_form.html', {
        'form': form,
        'systematic': systematic
    })
    

def equipamentos_por_linha(request):  #filtro equipamentos por linha
    line_id = request.GET.get('line_id')
    equipamentos = Equipment.objects.filter(line_id=line_id).values('id', 'name')
    return JsonResponse(list(equipamentos), safe=False)

@group_required('Administrador', 'Técnico')
def systematic_create_view(request): #Nova sistematica
    if request.method == 'POST':
        form = SystematicForm(request.POST)
        if form.is_valid() and formset.is_valid():
            systematic = form.save(commit=False)
            systematic.created_by = request.user
            systematic.save()
            formset.instance =  systematic
            formset.save()
            messages.success(request, f'Sistemática"{systematic.name}" criada com sucesso!')
            return redirect(reverse('core:systematic_detail', args=[systematic.pk]))
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = SystematicForm()
        formset = SystematicPartFormSet()
        
    return render(request, 'core/systematic_form.html', {
        'form': form,
        'formset': formset,
    })
    
@group_required('Administrador', 'Técnico')
def create_part_view(request):
    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            part = form.save()
            messages.success(request, f'Peça "{part.name}" criada com sucesso!')
            # Redireciona para onde estava (URL anterior)
            return redirect(request.GET.get('next', 'core:systematic_create'))
    else:
        form = PartForm()

    return render(request, 'core/part_form.html', {
        'form': form,
    })

def dashboard_drilldown_view(request):
    hoje = timezone.now().date()
    linhas = Line.objects.all()
    dashboard_data = []

    for linha in linhas:
        sistematicas = Systematic.objects.filter(equipment__line=linha, is_active=True)
        total = sistematicas.count()

        concluidas = atrasadas = programadas = 0

        for s in sistematicas:
            status = s.get_overall_status()
            if status.startswith("Atrasada"):
                atrasadas += 1
            elif "Pendente" in status or "Próxima" in status:
                programadas += 1
            elif "Em Dia" in status or "Concluída" in status:
                concluidas += 1

        if total > 0:
            dashboard_data.append({
                'linha': linha.name,
                'id': linha.pk,
                'total': total,
                'concluidas': concluidas,
                'atrasadas': atrasadas,
                'programadas': programadas,
                'percentual_concluidas': round((concluidas / total) * 100, 1),
                'percentual_atrasadas': round((atrasadas / total) * 100, 1),
                'percentual_programadas': round((programadas / total) * 100, 1),
            })

    return render(request, 'core/dashboard_drilldown.html', {'linhas': dashboard_data})

def sistematicas_por_equipamento(request):
    
    equip_id = request.GET.get('equipment_id')
    sistematicas = Systematic.objects.filter(equipment_id=equip_id, is_active=True)

    data = []
    for s in sistematicas:
        data.append({
            'id': s.pk,
            'name': s.name,
            'status': s.get_overall_status(),
            'next_execution': s.next_execution_date_calculated.strftime('%d/%m/%Y') if s.next_execution_date_calculated else '—',
            'detail_url': reverse('core:systematic_detail', args=[s.pk]),
            'exec_url': reverse('core:register_execution', args=[s.pk])
        })

    return JsonResponse(data, safe=False)

@require_POST
def create_part_ajax(request):
    name = request.POST.get('name')
    sap_code = request.POST.get('sap_code')

    if not name or not sap_code:
        return JsonResponse({'success': False, 'message': 'Todos os campos são obrigatórios.'})

    part, created = Part.objects.get_or_create(name=name, sap_code=sap_code)
    
    return JsonResponse({
        'success': True,
        'id': part.id,
        'name': f"{part.name} ({part.sap_code})"
    })
    
@require_POST
def create_equipment_ajax(request):
    name = request.POST.get('name')
    line_id = request.POST.get('line_id')


    if not name or not line_id:
        return JsonResponse({'success': False, 'message': 'Todos os campos são obrigatórios.'})

    try:
        line = Line.objects.get(pk=line_id)
    except Line.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Linha não encontrada.'})

  
    equipment, created = Equipment.objects.get_or_create(name=name, line=line)

    return JsonResponse({
        'success': True,
        'id': equipment.id,
        'name': f'{equipment.name} ({line.name})'
    })
    