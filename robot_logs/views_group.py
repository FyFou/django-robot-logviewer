from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.db.models import Count, Q, Min, Max
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import LogGroup, RobotLog, MDFFile
from .forms import LogGroupForm, AssignLogsToGroupForm

import json
import logging

logger = logging.getLogger(__name__)

class LogGroupListView(ListView):
    """Vue pour afficher la liste des groupes de logs, utilisée comme page d'accueil"""
    model = LogGroup
    template_name = 'robot_logs/log_group_list.html'
    context_object_name = 'log_groups'
    paginate_by = 20
    
    def get_queryset(self):
        """Retourne les groupes avec un tri explicite"""
        queryset = super().get_queryset().order_by('-created_at')
        
        # Filtrer par tag si fourni
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__icontains=tag)
            
        # Filtrer par robot_id si fourni
        robot_id = self.request.GET.get('robot_id')
        if robot_id:
            queryset = queryset.filter(robot_id=robot_id)
            
        # Recherche dans le nom ou la description
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
            
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer tous les tags uniques pour le filtre
        tags = set()
        for group in LogGroup.objects.exclude(tags__isnull=True).exclude(tags=''):
            if group.tags:
                for tag in group.tags.split(','):
                    tags.add(tag.strip())
        
        context['tags'] = sorted(tags)
        context['robot_ids'] = LogGroup.objects.exclude(robot_id__isnull=True).values_list('robot_id', flat=True).distinct()
        
        # Ajouter le formulaire de création de groupe
        context['form'] = LogGroupForm()
        
        # Statistiques pour la page d'accueil
        context['total_logs'] = RobotLog.objects.count()
        context['total_groups'] = LogGroup.objects.count()
        context['logs_in_groups'] = RobotLog.objects.filter(group__isnull=False).count()
        context['orphan_logs'] = RobotLog.objects.filter(group__isnull=True).count()
        context['mdf_files_count'] = MDFFile.objects.count()
        
        # Compter par type de log
        log_types_count = {}
        for log_type, name in RobotLog.LOG_TYPES:
            log_types_count[log_type] = RobotLog.objects.filter(log_type=log_type).count()
        context['log_types_count'] = log_types_count
        context['log_types_dict'] = dict(RobotLog.LOG_TYPES)
        
        # Compter par niveau de log
        log_levels_count = {}
        for level, name in RobotLog.LOG_LEVELS:
            log_levels_count[level] = RobotLog.objects.filter(level=level).count()
        context['log_levels_count'] = log_levels_count
        context['log_levels_dict'] = dict(RobotLog.LOG_LEVELS)
        
        return context

class LogGroupDetailView(DetailView):
    """Vue pour afficher les détails d'un groupe et ses logs"""
    model = LogGroup
    template_name = 'robot_logs/log_group_detail.html'
    context_object_name = 'log_group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log_group = self.get_object()
        
        # Récupérer les logs associés à ce groupe avec pagination
        logs = log_group.logs.all()
        
        # Filtrer les logs si nécessaire
        level = self.request.GET.get('level')
        if level:
            logs = logs.filter(level=level)
            
        log_type = self.request.GET.get('log_type')
        if log_type:
            logs = logs.filter(log_type=log_type)
            
        search = self.request.GET.get('search')
        if search:
            logs = logs.filter(
                Q(message__icontains=search) | 
                Q(source__icontains=search)
            )
        
        # Ajouter les logs filtrés au contexte
        context['logs'] = logs
        
        # Ajouter des statistiques sur les logs
        context['log_count'] = logs.count()
        context['log_types_count'] = {log_type: count for log_type, count in logs.values_list('log_type').annotate(count=Count('id'))}
        context['log_levels_count'] = {level: count for level, count in logs.values_list('level').annotate(count=Count('id'))}
        
        # Ajouter les dictionnaires de choix pour les filtres
        context['log_levels_dict'] = dict(RobotLog.LOG_LEVELS)
        context['log_types_dict'] = dict(RobotLog.LOG_TYPES)
        
        # Ajouter le formulaire de modification
        context['form'] = LogGroupForm(instance=log_group)
        
        # Vérifier si ce groupe est associé à un fichier MDF
        context['mdf_files'] = log_group.mdf_files.all() if hasattr(log_group, 'mdf_files') else []
        
        return context

class LogGroupCreateView(CreateView):
    """Vue pour créer un nouveau groupe de logs"""
    model = LogGroup
    form_class = LogGroupForm
    template_name = 'robot_logs/log_group_form.html'
    
    def get_success_url(self):
        return reverse('robot_logs:log_group_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Groupe '{form.instance.name}' créé avec succès.")
        return super().form_valid(form)

class LogGroupUpdateView(UpdateView):
    """Vue pour modifier un groupe de logs existant"""
    model = LogGroup
    form_class = LogGroupForm
    template_name = 'robot_logs/log_group_form.html'
    
    def get_success_url(self):
        return reverse('robot_logs:log_group_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Groupe '{form.instance.name}' mis à jour.")
        return super().form_valid(form)

class LogGroupDeleteView(DeleteView):
    """Vue pour supprimer un groupe de logs"""
    model = LogGroup
    template_name = 'robot_logs/log_group_confirm_delete.html'
    success_url = reverse_lazy('robot_logs:home')  # Rediriger vers la page d'accueil
    
    def delete(self, request, *args, **kwargs):
        log_group = self.get_object()
        name = log_group.name
        
        # Option: définir group=None pour tous les logs associés au lieu de les supprimer
        log_group.logs.update(group=None)
        
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f"Groupe '{name}' supprimé. Les logs associés ont été détachés du groupe.")
        return result

class AssignLogsToGroupView(View):
    """Vue pour assigner des logs sélectionnés à un groupe"""
    
    def post(self, request):
        # Récupérer les IDs des logs sélectionnés
        log_ids = request.POST.getlist('log_ids')
        
        if not log_ids:
            messages.error(request, "Aucun log sélectionné.")
            return redirect('robot_logs:log_list')
        
        form = AssignLogsToGroupForm(request.POST)
        
        if form.is_valid():
            group = form.cleaned_data.get('group')
            new_group_name = form.cleaned_data.get('new_group_name')
            
            # Créer un nouveau groupe si nécessaire
            if new_group_name:
                group = LogGroup(
                    name=new_group_name,
                    description=form.cleaned_data.get('new_group_description', '')
                )
                group.save()
                messages.success(request, f"Nouveau groupe '{new_group_name}' créé.")
            
            # Assigner les logs au groupe
            count = RobotLog.objects.filter(id__in=log_ids).update(group=group)
            
            if count:
                messages.success(request, f"{count} logs assignés au groupe '{group.name}'.")
                
                # Mettre à jour les dates de début et de fin du groupe basées sur les logs
                first_log = RobotLog.objects.filter(group=group).order_by('timestamp').first()
                last_log = RobotLog.objects.filter(group=group).order_by('-timestamp').first()
                
                if first_log and not group.start_time:
                    group.start_time = first_log.timestamp
                
                if last_log and not group.end_time:
                    group.end_time = last_log.timestamp
                
                # Définir robot_id du groupe si non défini
                if not group.robot_id:
                    # Utiliser le robot_id le plus fréquent dans les logs
                    robot_counts = RobotLog.objects.filter(group=group).values('robot_id').annotate(
                        count=Count('id')).order_by('-count')
                    if robot_counts:
                        group.robot_id = robot_counts[0]['robot_id']
                
                group.save()
                
                return redirect('robot_logs:log_group_detail', pk=group.id)
            else:
                messages.error(request, "Erreur lors de l'assignation des logs.")
        else:
            messages.error(request, "Formulaire invalide. Veuillez réessayer.")
        
        return redirect('robot_logs:log_list')

class RemoveLogsFromGroupView(View):
    """Vue pour retirer des logs d'un groupe"""
    
    def post(self, request, group_id):
        group = get_object_or_404(LogGroup, id=group_id)
        log_ids = request.POST.getlist('log_ids')
        
        if not log_ids:
            messages.error(request, "Aucun log sélectionné.")
            return redirect('robot_logs:log_group_detail', pk=group_id)
        
        count = RobotLog.objects.filter(id__in=log_ids, group=group).update(group=None)
        
        if count:
            messages.success(request, f"{count} logs retirés du groupe '{group.name}'.")
        else:
            messages.error(request, "Aucun log n'a pu être retiré du groupe.")
            
        return redirect('robot_logs:log_group_detail', pk=group_id)

class MergeLGroupsView(View):
    """Vue pour fusionner plusieurs groupes de logs"""
    
    def post(self, request):
        group_ids = request.POST.getlist('group_ids')
        target_group_id = request.POST.get('target_group')
        
        if not group_ids or not target_group_id:
            messages.error(request, "Sélection invalide. Veuillez choisir des groupes à fusionner et un groupe cible.")
            return redirect('robot_logs:home')
        
        # Vérifier que le groupe cible est dans la liste des groupes à fusionner
        if target_group_id not in group_ids:
            messages.error(request, "Le groupe cible doit faire partie des groupes sélectionnés.")
            return redirect('robot_logs:home')
        
        target_group = get_object_or_404(LogGroup, id=target_group_id)
        groups_to_merge = LogGroup.objects.filter(id__in=group_ids).exclude(id=target_group_id)
        
        # Déplacer tous les logs des autres groupes vers le groupe cible
        log_count = 0
        for group in groups_to_merge:
            # Mettre à jour les logs
            updated = group.logs.update(group=target_group)
            log_count += updated
            
            # Mettre à jour les fichiers MDF si présents
            if hasattr(group, 'mdf_files'):
                group.mdf_files.update(log_group=target_group)
            
            # Supprimer le groupe source
            group_name = group.name
            group.delete()
            messages.info(request, f"Groupe '{group_name}' fusionné et supprimé.")
        
        if log_count:
            messages.success(request, f"{log_count} logs transférés au groupe '{target_group.name}'.")
        
        # Rediriger vers le groupe cible
        return redirect('robot_logs:log_group_detail', pk=target_group.id)
