from django.contrib import admin
from .models import (
    Line, Equipment, Part, TipoSystematic, Systematic, 
    SystematicPartRequired, ExecutionRecord
)

# Inline de peças por sistemática
class SystematicPartRequiredInline(admin.TabularInline):
    model = SystematicPartRequired
    extra = 1
    autocomplete_fields = ['part']
    fields = ['part', 'quantity_required', 'observation']
    verbose_name = "Peça Necessária"
    verbose_name_plural = "Peças Necessárias"

# Linhas
@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Equipamentos
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'line')
    list_filter = ('line',)
    search_fields = ('name', 'line__name')

# Peças
@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('name', 'sap_code')
    search_fields = ('name', 'sap_code')

# Tipos de Sistemática
@admin.register(TipoSystematic)
class TipoSystematicAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao', 'created_at')
    search_fields = ('nome',)

# Sistemáticas
@admin.register(Systematic)
class SystematicAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'tipo_systematic', 'equipment', 
        'range_days', 'get_status', 'next_execution_date_calculated', 
        'is_active', 'created_by', 'created_at'
    )
    search_fields = ('name', 'equipment__name', 'tipo_systematic__nome')
    list_filter = ('tipo_systematic', 'equipment__line', 'is_active')
    readonly_fields = (
        'created_at', 'updated_at', 
        'last_execution_date_display', 'next_execution_date_calculated'
    )
    inlines = [SystematicPartRequiredInline]

    def get_status(self, obj):
        return obj.get_overall_status()
    get_status.short_description = 'Status'

# Execuções
@admin.register(ExecutionRecord)
class ExecutionRecordAdmin(admin.ModelAdmin):
    list_display = (
        'systematic', 'scheduled_date', 'execution_start_date', 
        'execution_end_date', 'executed_by', 'status'
    )
    list_filter = ('status', 'systematic__equipment__line', 'scheduled_date')
    search_fields = ('systematic__name', 'executed_by__username')
    autocomplete_fields = ['systematic', 'executed_by']
    readonly_fields = ('created_at', 'updated_at')

