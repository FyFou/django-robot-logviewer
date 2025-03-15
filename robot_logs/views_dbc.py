"""
Module contenant les vues pour la gestion des fichiers DBC.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, View
from django.contrib import messages
import logging

from .models import DBCFile
from .forms import DBCFileForm

logger = logging.getLogger(__name__)

class DBCFileListView(ListView):
    """Vue pour afficher la liste des fichiers DBC"""
    
    model = DBCFile
    template_name = 'robot_logs/dbc_file_list.html'
    context_object_name = 'dbc_files'
    paginate_by = 20
    
    def get_queryset(self):
        """Retourne les fichiers DBC triés par date de téléchargement"""
        return super().get_queryset().order_by('-uploaded_at')

class DBCFileUploadView(View):
    """Vue pour télécharger des fichiers DBC"""
    
    def get(self, request):
        """Affiche le formulaire de téléchargement"""
        form = DBCFileForm()
        return render(request, 'robot_logs/upload_dbc.html', {'form': form})
    
    def post(self, request):
        """Traite le formulaire de téléchargement"""
        form = DBCFileForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Enregistrer le fichier DBC
                dbc_file = form.save()
                
                # Afficher un message de succès
                messages.success(
                    request, 
                    f"Fichier DBC '{dbc_file.name}' téléchargé avec succès."
                )
                
                return redirect('robot_logs:dbc_file_list')
                
            except Exception as e:
                # Journaliser l'erreur
                logger.error(f"Erreur lors du téléchargement du fichier DBC: {e}", exc_info=True)
                
                # Afficher un message d'erreur
                messages.error(
                    request, 
                    f"Erreur lors du téléchargement: {str(e)}"
                )
        
        # Si le formulaire n'est pas valide, réafficher avec les erreurs
        return render(request, 'robot_logs/upload_dbc.html', {'form': form})

class DBCFileDetailView(View):
    """Vue pour afficher les détails d'un fichier DBC"""
    
    def get(self, request, pk):
        """Affiche les détails d'un fichier DBC"""
        dbc_file = get_object_or_404(DBCFile, pk=pk)
        
        # Tenter de charger et parser le fichier DBC pour afficher ses informations
        try:
            from .can_parser import DBCParser
            
            # Initialiser le parser DBC
            parser = DBCParser(dbc_file.file.path)
            
            # Si nous utilisons cantools, récupérer des informations supplémentaires
            if hasattr(parser, 'use_cantools') and parser.use_cantools and hasattr(parser, 'db'):
                # Extraire les informations sur les messages
                messages_info = []
                for message in parser.db.messages:
                    messages_info.append({
                        'id': hex(message.frame_id),
                        'name': message.name,
                        'length': message.length,
                        'signals_count': len(message.signals),
                        'comment': message.comment if hasattr(message, 'comment') else ''
                    })
                
                context = {
                    'dbc_file': dbc_file,
                    'messages': messages_info,
                    'messages_count': len(messages_info),
                    'parser_type': 'cantools'
                }
            else:
                # Parser de base
                messages_info = []
                for can_id, message_info in parser.messages.items():
                    messages_info.append({
                        'id': hex(can_id),
                        'name': message_info.get('name', 'Inconnu'),
                        'length': message_info.get('length', 0),
                        'signals_count': len(message_info.get('signals', {})),
                        'comment': ''
                    })
                
                context = {
                    'dbc_file': dbc_file,
                    'messages': messages_info,
                    'messages_count': len(messages_info),
                    'parser_type': 'basic'
                }
        
        except Exception as e:
            # En cas d'erreur, afficher un message et les informations de base
            logger.error(f"Erreur lors du parsing du fichier DBC: {e}", exc_info=True)
            messages.warning(request, f"Impossible de parser le fichier DBC: {str(e)}")
            
            context = {
                'dbc_file': dbc_file,
                'error': str(e)
            }
        
        return render(request, 'robot_logs/dbc_file_detail.html', context)

class DBCFileDeleteView(View):
    """Vue pour supprimer un fichier DBC"""
    
    def post(self, request, pk):
        """Supprime un fichier DBC"""
        dbc_file = get_object_or_404(DBCFile, pk=pk)
        
        try:
            # Vérifier si le fichier est utilisé par des fichiers MDF
            if dbc_file.mdf_files.exists():
                messages.error(
                    request, 
                    f"Impossible de supprimer ce fichier DBC car il est utilisé par {dbc_file.mdf_files.count()} fichier(s) MDF."
                )
                return redirect('robot_logs:dbc_file_detail', pk=pk)
            
            # Supprimer le fichier
            name = dbc_file.name
            dbc_file.delete()
            
            # Afficher un message de succès
            messages.success(request, f"Fichier DBC '{name}' supprimé avec succès.")
            
        except Exception as e:
            # Journaliser l'erreur
            logger.error(f"Erreur lors de la suppression du fichier DBC: {e}", exc_info=True)
            
            # Afficher un message d'erreur
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
        
        return redirect('robot_logs:dbc_file_list')
