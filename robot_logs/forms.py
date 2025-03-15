from django import forms
from .models import MDFFile, DBCFile

class MDFImportForm(forms.ModelForm):
    """Formulaire pour importer un fichier MDF"""
    
    preview_first = forms.BooleanField(
        label="Prévisualiser d'abord",
        help_text="Voir le contenu du fichier avant l'importation",
        required=False,
        initial=True
    )
    
    dbc_file = forms.ModelChoiceField(
        queryset=DBCFile.objects.all(),
        label="Fichier DBC (pour décodage CAN)",
        required=False,
        help_text="Sélectionnez un fichier DBC pour décoder les traces CAN",
        empty_label="Aucun (pas de décodage CAN)"
    )
    
    class Meta:
        model = MDFFile
        fields = ['file', 'name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = "Nom descriptif pour ce fichier MDF"
        self.fields['file'].help_text = "Fichier MDF (format Vector MDF3 ou MDF4)"
        
    def clean_file(self):
        """Valide le fichier MDF"""
        file = self.cleaned_data.get('file')
        
        # Vérifier que le fichier existe
        if not file:
            raise forms.ValidationError("Aucun fichier n'a été sélectionné.")
        
        # Vérifier la taille du fichier
        if file.size == 0:
            raise forms.ValidationError("Le fichier soumis est vide.")
            
        # Afficher des informations de débogage sur le fichier
        print(f"Fichier soumis: {file.name}, taille: {file.size} octets")
        
        # Vérifier l'extension
        if file and not (file.name.lower().endswith('.mdf') or file.name.lower().endswith('.mf4')):
            raise forms.ValidationError("Le fichier doit être au format MDF (.mdf ou .mf4)")
        
        return file
        
    def clean(self):
        """Valide le formulaire complet"""
        cleaned_data = super().clean()
        
        # Si aucun nom n'est fourni, utiliser le nom du fichier
        if 'file' in cleaned_data and not cleaned_data.get('name'):
            file = cleaned_data['file']
            cleaned_data['name'] = file.name
            self.cleaned_data['name'] = file.name
            
        return cleaned_data

class DBCFileForm(forms.ModelForm):
    """Formulaire pour importer un fichier DBC"""
    
    class Meta:
        model = DBCFile
        fields = ['file', 'name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = "Nom descriptif pour ce fichier DBC"
        self.fields['description'].help_text = "Description optionnelle (ex: version, véhicule concerné)"
        self.fields['file'].help_text = "Fichier DBC (.dbc)"
        
    def clean_file(self):
        """Valide le fichier DBC"""
        file = self.cleaned_data.get('file')
        
        # Vérifier que le fichier existe
        if not file:
            raise forms.ValidationError("Aucun fichier n'a été sélectionné.")
        
        # Vérifier la taille du fichier
        if file.size == 0:
            raise forms.ValidationError("Le fichier soumis est vide.")
            
        # Vérifier l'extension
        if file and not file.name.lower().endswith('.dbc'):
            raise forms.ValidationError("Le fichier doit être au format DBC (.dbc)")
        
        return file
        
    def clean(self):
        """Valide le formulaire complet"""
        cleaned_data = super().clean()
        
        # Si aucun nom n'est fourni, utiliser le nom du fichier
        if 'file' in cleaned_data and not cleaned_data.get('name'):
            file = cleaned_data['file']
            cleaned_data['name'] = file.name
            self.cleaned_data['name'] = file.name
            
        return cleaned_data
