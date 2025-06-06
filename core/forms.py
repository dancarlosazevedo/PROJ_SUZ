from django import forms
from .models import Systematic, TipoSystematic, Equipment, ExecutionRecord

class SystematicForm(forms.ModelForm):
    class Meta:
        model = Systematic
        fields = [
            'name',
            'tipo_systematic',
            'equipment',
            'description',
            'range_days',
            'time_estimated_minutes',
            'safety_instructions',
            'is_active',
        ]
        
        widget ={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_systematic': forms.Select(attrs={'class': 'form-select'}),
            'equipment': forms.Select(attrs={'class': 'form-select'}),
            'range_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_estimated_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'safety_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Nome da Sistemática',
            'tipo_systematic': 'Tipo de Sistemática',
            'equipment': 'Equipamento',
            'description': 'Descrição do Procedimento',
            'range_days': 'Frequência (dias)',
            'time_estimated_minutes': 'Tempo Estimado (minutos)',
            'safety_instructions': 'Instruções de Segurança',
            'needs_equipment_stop': 'Requer Parada do Equipamento?',
            'is_active': 'Sistemática Ativa?',
        }
        
class ExecutionRecordForm(forms.ModelForm):
    class Meta:
        model = ExecutionRecord
        fields = ['scheduled_date', 'execution_start_date', 'execution_end_date', 'status', 'observations']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'execution_start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'execution_end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }