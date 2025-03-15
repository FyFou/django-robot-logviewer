from django import forms
from .models import MDFFile, DBCFile, CANMapping

class MDFImportForm(forms.ModelForm):
    """Formulaire pour l'importation de fichiers MDF"""
    preview_first = forms.BooleanField(required=False, initial=True, label="Prévisualiser avant d'importer")
    
    class Meta:
        model = MDFFile
        fields = ['file', 'name', 'preview_first']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        self.fields['file'].widget.attrs.update({'class': 'form-control'})
        self.fields['preview_first'].widget.attrs.update({'class': 'form-check-input'})

class DBCUploadForm(forms.ModelForm):
    """Formulaire pour l'upload de fichiers DBC"""
    
    class Meta:
        model = DBCFile
        fields = ['file', 'name', 'description']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['file'].widget.attrs.update({'class': 'form-control'})
        
        # Rendre la description optionnelle
        self.fields['description'].required = False

class CANMappingForm(forms.ModelForm):
    """Formulaire pour associer des canaux CAN avec des fichiers DBC"""
    
    class Meta:
        model = CANMapping
        fields = ['mdf_file', 'channel_name', 'dbc_file']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mdf_file'].widget.attrs.update({'class': 'form-control'})
        self.fields['channel_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['dbc_file'].widget.attrs.update({'class': 'form-control'})
        
        # Ajouter des étiquettes plus explicites
        self.fields['mdf_file'].label = "Fichier MDF"
        self.fields['channel_name'].label = "Nom du canal CAN"
        self.fields['dbc_file'].label = "Fichier DBC à associer"
        
        # Ajouter des aides
        self.fields['channel_name'].help_text = "Le nom complet ou le préfixe du canal CAN dans le fichier MDF"
        
        # Option None pour le fichier DBC (permettre de supprimer l'association)
        self.fields['dbc_file'].required = False
        self.fields['dbc_file'].empty_label = "Aucun (supprimer l'association)"
