# Generated by Django 5.2.1 on 2025-06-02 00:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='systematic',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Sistemática Ativa?'),
        ),
    ]
