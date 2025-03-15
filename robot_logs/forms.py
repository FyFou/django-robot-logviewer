from django import forms
from .models import MDFFile, DBCFile, CANMapping

class MDFImportForm(forms.ModelForm):
    """Formulaire pour importer un fichier MDF"""
    preview_first = forms.BooleanField(
        required=False, 
        initial=True,
        label="Prévisualiser le contenu avant importation",
        help_text="Affiche un aperçu des canaux contenus dans le fichier MDF avant de les importer"
    )
    
    class Meta:
        model = MDFFile
        fields = ['file', 'name', 'preview_first']
        labels = {
            'file': 'Fichier MDF',
            'name': 'Nom'
        }
        help_texts = {
            'file': 'Sélectionnez un fichier MDF à importer (.mdf, .mf4)',
            'name': 'Nom descriptif pour ce fichier'
        }

class DBCImportForm(forms.ModelForm):
    """Formulaire pour importer un fichier DBC"""
    class Meta:
        model = DBCFile
        fields = ['file', 'name', 'description']
        labels = {
            'file': 'Fichier DBC',
            'name': 'Nom',
            'description': 'Description'
        }
        help_texts = {
            'file': 'Sélectionnez un fichier DBC (Database CAN) à importer (.dbc)',
            'name': 'Nom descriptif pour ce fichier',
            'description': 'Description optionnelle (e.g. version du véhicule, ECU, etc.)'
        }

class CANMappingForm(forms.ModelForm):
    """Formulaire pour associer un canal CAN à un fichier DBC"""
    class Meta:
        model = CANMapping
        fields = ['mdf_file', 'channel_name', 'dbc_file']
        labels = {
            'mdf_file': 'Fichier MDF',
            'channel_name': 'Nom du canal CAN',
            'dbc_file': 'Fichier DBC'
        }
        help_texts = {
            'mdf_file': 'Fichier MDF contenant le canal CAN',
            'channel_name': 'Nom du canal CAN dans le fichier MDF',
            'dbc_file': 'Fichier DBC à utiliser pour décoder ce canal'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si un fichier MDF est déjà sélectionné, filtrer les canaux disponibles
        if 'mdf_file' in self.initial:
            mdf_file = self.initial['mdf_file']
            # Ici, on pourrait ajouter une logique pour ajouter des choix pour channel_name
            # basés sur les canaux CAN détectés dans le fichier MDF
