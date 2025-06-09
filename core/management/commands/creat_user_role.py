from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Systematic, ExecutionRecord

class Command(BaseCommand):
    help = ' Cria grupos de usuários e define permissões'
    
    def handle(self, **args, **kwargs):
        #Grupo de administrador
        admin_group,_ = Group.objects.get_or_create(name='Administrador')
        admin_permissions = Permission.objects.all()
        admin_group.permissions.set(admin_permissions)
        
        #Grupo execução/tecnico
        tecnico_group,_ = Group.objects.get_or_create(name = 'Técnico')
        tecnico_permissions = Permission.objects.filter(
            content_type_model__in=['executionredord'],
            codename__startswith=('add')
        )
        tecnico_group.permissions.set(tecnico_perms)
        
        visual_group, _ = Group.objects.get_or_create(name='Visualizador')
        visual_perms = Permission.objects.filter(codename__startswith='view')
        visual_group.permissions.set(visual_perms)

        self.stdout.write(self.style.SUCCESS('Grupos criados e permissões aplicadas com sucesso!'))