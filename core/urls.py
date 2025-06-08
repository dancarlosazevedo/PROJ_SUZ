from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('', views.calendario_view, name='home_calendario'),
    path('api/calendar-events/', views.calendar_events_api, name='calendar_events_api'),#Eventos do calendário
    path('sistematica/<int:pk>', views.systematic_detail_view, name ='systematic_detail'),
    path('sistematica/<int:pk>/editar/', views.systematic_edit_view, name='systematic_edit'), #formulario de edidção da sistematica
    path('sistematica/<int:pk>/registrar-execucao/', views.register_execution_view, name='register_execution'), #botão de execução
    path('api/equipamentos-por-linha/', views.equipamentos_por_linha, name='equipamentos_por_linha'),
    path('sistematica/nova/', views.systematic_create_view, name='systematic_create'), #formulario nova sistematica
    path('peca/nova/', views.create_part_view, name='create_part'),
    path('painel/', views.dashboard_drilldown_view, name='dashboard_drilldown'),
    path('api/sistematicas-do-equipamento/', views.sistematicas_por_equipamento, name='sistematicas_por_equipamento'), #Drill down do equipamento


    
]
