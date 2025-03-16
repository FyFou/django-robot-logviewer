from django import forms
from .models import MDFFile, LogGroup, RobotLog
from django.utils import timezone

class MDFImportForm(forms.ModelForm):
    preview_first = forms.BooleanField(
        label="Prévisualiser avant importation",
        required=False,
        initial=True,
        help_text="Cochez pour voir le contenu du fichier avant de l'importer"
    )
    
    class Meta:
        model = MDFFile
        fields = ['name', 'file']
        labels = {
            'name': 'Nom',
            'file': 'Fichier MDF',
        }
        help_texts = {
            'name': 'Nom descriptif pour identifier ce fichier',
            'file': 'Fichier MDF (.mf4, .mdf) à importer',
        }

class LogGroupForm(forms.ModelForm):
    """Formulaire pour créer ou modifier un groupe de logs"""
    
    class Meta:
        model = LogGroup
        fields = ['name', 'description', 'robot_id', 'tags', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'tags': 'Entrez des tags séparés par des virgules (par exemple: test, validation, erreur)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs non obligatoires
        self.fields['robot_id'].required = False
        self.fields['start_time'].required = False
        self.fields['end_time'].required = False

class AssignLogsToGroupForm(forms.Form):
    """Formulaire pour assigner des logs à un groupe existant"""
    
    group = forms.ModelChoiceField(
        queryset=LogGroup.objects.all().order_by('-created_at'),
        label="Groupe",
        help_text="Sélectionnez le groupe auquel assigner les logs",
        empty_label="Créer un nouveau groupe",
        required=False
    )
    
    new_group_name = forms.CharField(
        max_length=200,
        label="Nom du nouveau groupe",
        required=False,
        help_text="Si vous souhaitez créer un nouveau groupe, entrez son nom"
    )
    
    new_group_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Description",
        required=False
    )
    
    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get("group")
        new_group_name = cleaned_data.get("new_group_name")
        
        if not group and not new_group_name:
            raise forms.ValidationError(
                "Vous devez soit sélectionner un groupe existant, soit entrer un nom pour un nouveau groupe."
            )
        
        return cleaned_data

class LogFilterForm(forms.Form):
    """Formulaire pour filtrer les logs avec une option de groupe"""
    
    level = forms.ChoiceField(
        choices=[('', 'Tous les niveaux')] + list(RobotLog.LOG_LEVELS),
        required=False,
        label="Niveau"
    )
    
    log_type = forms.ChoiceField(
        choices=[('', 'Tous les types')] + list(RobotLog.LOG_TYPES),
        required=False,
        label="Type"
    )
    
    robot_id = forms.CharField(
        max_length=100,
        required=False,
        label="Robot ID"
    )
    
    search = forms.CharField(
        max_length=100,
        required=False,
        label="Recherche"
    )
    
    date_start = forms.DateTimeField(
        required=False,
        label="Date de début",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    
    date_end = forms.DateTimeField(
        required=False,
        label="Date de fin",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    
    group = forms.ModelChoiceField(
        queryset=LogGroup.objects.all(),
        required=False,
        label="Groupe",
        empty_label="Tous les groupes"
    )
