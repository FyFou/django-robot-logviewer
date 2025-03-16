# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('robot_logs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='loggroup',
            name='is_channel_group',
            field=models.BooleanField(default=False, help_text='Indique si ce groupe représente un channel group MDF'),
        ),
        migrations.AddField(
            model_name='loggroup',
            name='channel_group_index',
            field=models.IntegerField(blank=True, help_text='Index du channel group dans le fichier MDF', null=True),
        ),
        migrations.AddField(
            model_name='loggroup',
            name='parent_group',
            field=models.ForeignKey(blank=True, help_text='Groupe parent si ce groupe est un channel group', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='channel_groups', to='robot_logs.loggroup'),
        ),
        migrations.AddField(
            model_name='robotlog',
            name='channel_group_index',
            field=models.IntegerField(blank=True, help_text="Index du channel group d'origine dans le fichier MDF", null=True),
        ),
        migrations.AddField(
            model_name='mdffile',
            name='channel_groups_info',
            field=models.TextField(blank=True, help_text='Informations JSON sur les channel groups du fichier', null=True),
        ),
    ]
