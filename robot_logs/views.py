from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.http import HttpResponse
import csv
from .models import RobotLog

class LogListView(ListView):
    model = RobotLog
    template_name = 'robot_logs/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtre par niveau de log
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)
            
        # Filtre par robot_id
        robot_id = self.request.GET.get('robot_id')
        if robot_id:
            queryset = queryset.filter(robot_id=robot_id)
            
        # Recherche dans les messages
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(message__icontains=search) | 
                Q(source__icontains=search)
            )
            
        # Filtre par date
        date_start = self.request.GET.get('date_start')
        if date_start:
            queryset = queryset.filter(timestamp__gte=date_start)
            
        date_end = self.request.GET.get('date_end')
        if date_end:
            queryset = queryset.filter(timestamp__lte=date_end)
            
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['robot_ids'] = RobotLog.objects.values_list('robot_id', flat=True).distinct()
        context['log_levels'] = dict(RobotLog.LOG_LEVELS)
        return context

class LogDetailView(DetailView):
    model = RobotLog
    template_name = 'robot_logs/log_detail.html'
    context_object_name = 'log'

def export_logs_csv(request):
    # Utiliser les mêmes filtres que la vue de liste
    queryset = RobotLog.objects.all()
    
    level = request.GET.get('level')
    if level:
        queryset = queryset.filter(level=level)
        
    robot_id = request.GET.get('robot_id')
    if robot_id:
        queryset = queryset.filter(robot_id=robot_id)
        
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(message__icontains=search) | 
            Q(source__icontains=search)
        )
        
    date_start = request.GET.get('date_start')
    if date_start:
        queryset = queryset.filter(timestamp__gte=date_start)
        
    date_end = request.GET.get('date_end')
    if date_end:
        queryset = queryset.filter(timestamp__lte=date_end)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="robot_logs.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date/Heure', 'Robot ID', 'Niveau', 'Message', 'Source'])
    
    for log in queryset:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.robot_id,
            log.level,
            log.message,
            log.source
        ])
    
    return response
