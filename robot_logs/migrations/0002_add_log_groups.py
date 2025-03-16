from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('robot_logs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('robot_id', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('tags', models.CharField(blank=True, help_text='Tags séparés par des virgules pour faciliter la recherche', max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Groupe de logs',
                'verbose_name_plural': 'Groupes de logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='robotlog',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logs', to='robot_logs.loggroup'),
        ),
        migrations.AddField(
            model_name='mdffile',
            name='log_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mdf_files', to='robot_logs.loggroup'),
        ),
    ]
