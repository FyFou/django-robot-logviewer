"""
Vues pour gérer les fichiers DBC et mappings CAN
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
import logging
import os

from .models import DBCFile, CANMapping, MDFFile
from .forms import DBCImportForm, CANMappingForm
from .mdf_parsers.dbc_interpreter import DBCInterpreter, CANTOOLS_AVAILABLE

logger = logging.getLogger(__name__)

class DBCListView(ListView):
    """Vue pour afficher la liste des fichiers DBC importés"""
    model = DBCFile
    template_name = 'robot_logs/dbc_list.html'
    context_object_name = 'dbc_files'
    paginate_by = 20
    
    def get_queryset(self):
        return super().get_queryset().order_by('-uploaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cantools_available'] = CANTOOLS_AVAILABLE
        return context

class DBCDetailView(DetailView):
    """Vue pour afficher les détails d'un fichier DBC"""
    model = DBCFile
    template_name = 'robot_logs/dbc_detail.html'
    context_object_name = 'dbc_file'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dbc_file = self.get_object()
        
        # Récupérer les mappings CAN pour ce fichier DBC
        can_mappings = CANMapping.objects.filter(dbc_file=dbc_file)
        context['can_mappings'] = can_mappings
        
        # Si cantools est disponible, essayer de récupérer les informations sur les messages
        if CANTOOLS_AVAILABLE:
            dbc_interpreter = DBCInterpreter()
            if dbc_interpreter.load_dbc_file(dbc_file.file.path, dbc_file.id):
                # Récupérer tous les IDs de message définis dans le fichier DBC
                message_ids = dbc_interpreter.get_all_message_ids(dbc_file.id)
                if message_ids:
                    context['message_ids'] = message_ids
        
        return context

class ImportDBCView(View):
    """Vue pour importer un fichier DBC"""
    
    def get(self, request):
        """Affiche le formulaire d'importation"""
        form = DBCImportForm()
        return render(request, 'robot_logs/import_dbc.html', {'form': form})
    
    def post(self, request):
        """Traite le formulaire d'importation"""
        form = DBCImportForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Vérifier si cantools est disponible
            if not CANTOOLS_AVAILABLE:
                messages.warning(request, "La bibliothèque cantools n'est pas installée. "
                                 "Le fichier DBC sera importé, mais ne pourra pas être utilisé pour le décodage.")
            
            try:
                # Créer un nouvel objet DBCFile
                dbc_file = form.save()
                
                # Vérifier la validité du fichier DBC
                if CANTOOLS_AVAILABLE:
                    dbc_interpreter = DBCInterpreter()
                    if dbc_interpreter.load_dbc_file(dbc_file.file.path, dbc_file.id):
                        messages.success(request, f"Fichier DBC importé avec succès : {dbc_file.name}")
                    else:
                        messages.warning(request, f"Le fichier DBC a été importé, mais il semble invalide ou incomplet.")
                else:
                    messages.success(request, f"Fichier DBC importé avec succès : {dbc_file.name}")
                
                return redirect('robot_logs:dbc_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'importation du fichier DBC : {str(e)}")
        
        return render(request, 'robot_logs/import_dbc.html', {'form': form})

class DeleteDBCView(DeleteView):
    """Vue pour supprimer un fichier DBC"""
    model = DBCFile
    template_name = 'robot_logs/dbc_confirm_delete.html'
    success_url = reverse_lazy('robot_logs:dbc_list')
    
    def delete(self, request, *args, **kwargs):
        dbc_file = self.get_object()
        
        # Vérifier si le fichier DBC est utilisé dans des mappings
        can_mappings = CANMapping.objects.filter(dbc_file=dbc_file)
        if can_mappings.exists():
            messages.warning(request, f"Ce fichier DBC est utilisé par {can_mappings.count()} mappings CAN. "
                             "Les mappings ont été supprimés.")
            can_mappings.delete()
        
        # Supprimer le fichier DBC
        messages.success(request, f"Fichier DBC supprimé : {dbc_file.name}")
        return super().delete(request, *args, **kwargs)

class CANMappingListView(ListView):
    """Vue pour afficher la liste des mappings CAN"""
    model = CANMapping
    template_name = 'robot_logs/can_mapping_list.html'
    context_object_name = 'can_mappings'
    paginate_by = 20

class CreateCANMappingView(CreateView):
    """Vue pour créer un mapping CAN"""
    model = CANMapping
    form_class = CANMappingForm
    template_name = 'robot_logs/can_mapping_form.html'
    success_url = reverse_lazy('robot_logs:can_mapping_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Mapping CAN créé avec succès.")
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Si un fichier MDF est fourni en paramètre, le pré-sélectionner
        mdf_id = self.request.GET.get('mdf_id')
        if mdf_id:
            try:
                mdf_file = MDFFile.objects.get(id=mdf_id)
                form.initial['mdf_file'] = mdf_file
            except MDFFile.DoesNotExist:
                pass
        
        return form

class UpdateCANMappingView(UpdateView):
    """Vue pour modifier un mapping CAN"""
    model = CANMapping
    form_class = CANMappingForm
    template_name = 'robot_logs/can_mapping_form.html'
    success_url = reverse_lazy('robot_logs:can_mapping_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Mapping CAN mis à jour avec succès.")
        return super().form_valid(form)

class DeleteCANMappingView(DeleteView):
    """Vue pour supprimer un mapping CAN"""
    model = CANMapping
    template_name = 'robot_logs/can_mapping_confirm_delete.html'
    success_url = reverse_lazy('robot_logs:can_mapping_list')
    
    def delete(self, request, *args, **kwargs):
        can_mapping = self.get_object()
        messages.success(request, f"Mapping CAN supprimé pour {can_mapping.channel_name}")
        return super().delete(request, *args, **kwargs)

def get_dbc_messages(request, pk):
    """API pour récupérer les messages d'un fichier DBC"""
    dbc_file = get_object_or_404(DBCFile, pk=pk)
    
    if not CANTOOLS_AVAILABLE:
        return JsonResponse({'error': 'cantools not available'}, status=400)
    
    try:
        dbc_interpreter = DBCInterpreter()
        if dbc_interpreter.load_dbc_file(dbc_file.file.path, dbc_file.id):
            message_ids = dbc_interpreter.get_all_message_ids(dbc_file.id)
            if message_ids:
                return JsonResponse({'messages': message_ids})
        
        return JsonResponse({'error': 'Could not load DBC file'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_can_channels(request, pk):
    """API pour récupérer les canaux CAN d'un fichier MDF"""
    mdf_file = get_object_or_404(MDFFile, pk=pk)
    
    try:
        # Créer un parser MDF temporaire pour récupérer les canaux
        from .mdf_parsers import MDFParser
        from .mdf_parsers.utils import is_can_data
        
        parser = MDFParser(mdf_file.file.path, mdf_file)
        channels = parser.get_channels()
        
        # Filtrer pour ne garder que les canaux CAN
        can_channels = []
        for channel in channels:
            try:
                data, _ = parser._adapter.get_channel_data_and_timestamps(channel)
                if is_can_data(channel, data):
                    can_channels.append(channel)
            except:
                pass
        
        parser.close()
        
        return JsonResponse({'can_channels': can_channels})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
