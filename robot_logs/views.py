from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib import messages
import csv
import json
import os
import tempfile

from .models import RobotLog, CurveMeasurement, Laser2DScan, ImageData, MDFFile
from .mdf_parser import MDFParser
from .forms import MDFImportForm

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
        
        # Filtre par type de log
        log_type = self.request.GET.get('log_type')
        if log_type:
            queryset = queryset.filter(log_type=log_type)
            
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
        context['log_types'] = dict(RobotLog.LOG_TYPES)
        context['mdf_import_form'] = MDFImportForm()
        context['has_mdf_files'] = MDFFile.objects.exists()
        return context

class LogDetailView(DetailView):
    model = RobotLog
    template_name = 'robot_logs/log_detail.html'
    context_object_name = 'log'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log = self.get_object()
        
        # Ajouter les données associées en fonction du type de log
        if log.log_type == 'CURVE':
            context['curve_measurements'] = log.curve_measurements.all()
            context['has_curve_data'] = context['curve_measurements'].exists()
        elif log.log_type == 'LASER2D':
            context['laser_scan'] = log.laser_scans.first()
        elif log.log_type == 'IMAGE':
            context['image'] = log.images.first()
        
        # Ajouter les métadonnées
        context['metadata'] = log.get_metadata_as_dict()
        
        return context

def export_logs_csv(request):
    # Utiliser les mêmes filtres que la vue de liste
    queryset = RobotLog.objects.all()
    
    level = request.GET.get('level')
    if level:
        queryset = queryset.filter(level=level)
        
    robot_id = request.GET.get('robot_id')
    if robot_id:
        queryset = queryset.filter(robot_id=robot_id)
        
    log_type = request.GET.get('log_type')
    if log_type:
        queryset = queryset.filter(log_type=log_type)
        
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
    writer.writerow(['Date/Heure', 'Robot ID', 'Niveau', 'Type', 'Message', 'Source'])
    
    for log in queryset:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.robot_id,
            log.level,
            log.log_type,
            log.message,
            log.source
        ])
    
    return response

class ImportMDFView(View):
    """Vue pour importer un fichier MDF"""
    
    def get(self, request):
        """Affiche le formulaire d'importation"""
        form = MDFImportForm()
        return render(request, 'robot_logs/import_mdf.html', {'form': form})
    
    def post(self, request):
        """Traite le formulaire d'importation"""
        form = MDFImportForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Créer un nouvel objet MDFFile
            mdf_file = form.save()
            
            try:
                # Créer un fichier temporaire pour le traitement
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    for chunk in mdf_file.file.chunks():
                        tmp_file.write(chunk)
                    tmp_path = tmp_file.name
                
                # Traiter le fichier MDF
                parser = MDFParser(tmp_path, mdf_file)
                
                # Si l'option de prévisualisation est cochée, rediriger vers la page de prévisualisation
                if form.cleaned_data.get('preview_first', False):
                    # Stocker le chemin du fichier temporaire dans la session
                    request.session['tmp_mdf_path'] = tmp_path
                    request.session['mdf_file_id'] = mdf_file.id
                    return redirect('robot_logs:preview_mdf')
                
                # Sinon, traiter directement le fichier
                stats = parser.process_file()
                parser.close()
                
                # Supprimer le fichier temporaire
                os.unlink(tmp_path)
                
                # Afficher un message de succès
                messages.success(
                    request, 
                    f"Importation réussie ! "
                    f"{stats.get('text_logs', 0)} logs textuels, "
                    f"{stats.get('curve_logs', 0)} courbes, "
                    f"{stats.get('laser_logs', 0)} scans laser, "
                    f"{stats.get('image_logs', 0)} images importés."
                )
                
                return redirect('robot_logs:log_list')
                
            except Exception as e:
                # En cas d'erreur, supprimer le fichier MDF
                mdf_file.delete()
                
                # Supprimer le fichier temporaire s'il existe
                if 'tmp_path' in locals():
                    os.unlink(tmp_path)
                
                # Afficher un message d'erreur
                messages.error(request, f"Erreur lors de l'importation : {str(e)}")
                return redirect('robot_logs:import_mdf')
        
        # Si le formulaire n'est pas valide, réafficher la page avec les erreurs
        return render(request, 'robot_logs/import_mdf.html', {'form': form})

class PreviewMDFView(View):
    """Vue pour prévisualiser le contenu d'un fichier MDF avant importation"""
    
    def get(self, request):
        """Affiche la prévisualisation du fichier MDF"""
        # Récupérer le chemin du fichier temporaire et l'ID du fichier MDF depuis la session
        tmp_path = request.session.get('tmp_mdf_path')
        mdf_file_id = request.session.get('mdf_file_id')
        
        if not tmp_path or not mdf_file_id:
            messages.error(request, "Aucun fichier MDF en attente d'importation")
            return redirect('robot_logs:import_mdf')
        
        try:
            # Récupérer l'objet MDFFile
            mdf_file = get_object_or_404(MDFFile, id=mdf_file_id)
            
            # Créer le parser MDF
            parser = MDFParser(tmp_path, mdf_file)
            
            # Ouvrir le fichier MDF
            if not parser.open():
                messages.error(request, "Impossible d'ouvrir le fichier MDF")
                return redirect('robot_logs:import_mdf')
            
            # Récupérer la liste des canaux
            channels = parser.get_channels()
            
            # Récupérer les informations sur chaque canal
            channel_infos = []
            for channel in channels[:100]:  # Limiter à 100 canaux pour la prévisualisation
                info = parser.get_channel_info(channel)
                if info:
                    channel_infos.append(info)
            
            # Fermer le parser
            parser.close()
            
            # Afficher la prévisualisation
            return render(request, 'robot_logs/preview_mdf.html', {
                'mdf_file': mdf_file,
                'channel_count': len(channels),
                'channels': channel_infos,
                'limited_preview': len(channels) > 100
            })
            
        except Exception as e:
            # En cas d'erreur, nettoyer
            if 'parser' in locals() and parser:
                parser.close()
            
            # Supprimer le fichier temporaire
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
            # Supprimer les entrées de session
            if 'tmp_mdf_path' in request.session:
                del request.session['tmp_mdf_path']
            if 'mdf_file_id' in request.session:
                del request.session['mdf_file_id']
            
            # Afficher un message d'erreur
            messages.error(request, f"Erreur lors de la prévisualisation : {str(e)}")
            return redirect('robot_logs:import_mdf')
    
    def post(self, request):
        """Traite l'importation après prévisualisation"""
        # Récupérer le chemin du fichier temporaire et l'ID du fichier MDF depuis la session
        tmp_path = request.session.get('tmp_mdf_path')
        mdf_file_id = request.session.get('mdf_file_id')
        
        if not tmp_path or not mdf_file_id:
            messages.error(request, "Aucun fichier MDF en attente d'importation")
            return redirect('robot_logs:import_mdf')
        
        try:
            # Récupérer l'objet MDFFile
            mdf_file = get_object_or_404(MDFFile, id=mdf_file_id)
            
            # Créer le parser MDF
            parser = MDFParser(tmp_path, mdf_file)
            
            # Traiter le fichier
            stats = parser.process_file()
            parser.close()
            
            # Supprimer le fichier temporaire
            os.unlink(tmp_path)
            
            # Supprimer les entrées de session
            del request.session['tmp_mdf_path']
            del request.session['mdf_file_id']
            
            # Afficher un message de succès
            messages.success(
                request, 
                f"Importation réussie ! "
                f"{stats.get('text_logs', 0)} logs textuels, "
                f"{stats.get('curve_logs', 0)} courbes, "
                f"{stats.get('laser_logs', 0)} scans laser, "
                f"{stats.get('image_logs', 0)} images importés."
            )
            
            return redirect('robot_logs:log_list')
            
        except Exception as e:
            # En cas d'erreur, nettoyer
            if 'parser' in locals() and parser:
                parser.close()
            
            # Supprimer le fichier temporaire
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
            # Supprimer les entrées de session
            if 'tmp_mdf_path' in request.session:
                del request.session['tmp_mdf_path']
            if 'mdf_file_id' in request.session:
                del request.session['mdf_file_id']
            
            # Afficher un message d'erreur
            messages.error(request, f"Erreur lors de l'importation : {str(e)}")
            return redirect('robot_logs:import_mdf')

class CurveDataView(View):
    """Vue pour afficher les données de courbe"""
    
    def get(self, request, log_id):
        log = get_object_or_404(RobotLog, id=log_id, log_type='CURVE')
        curve_data = log.curve_measurements.all()
        
        # Préparer les données pour Chart.js
        timestamps = [data.timestamp.timestamp() * 1000 for data in curve_data]  # Convertir en millisecondes pour JS
        values = [float(data.value) for data in curve_data]
        
        chart_data = {
            'timestamps': timestamps,
            'values': values,
            'sensor_name': curve_data.first().sensor_name if curve_data.exists() else "",
        }
        
        # Si demandé en JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(chart_data)
        
        # Sinon, afficher la page
        return render(request, 'robot_logs/curve_view.html', {
            'log': log,
            'chart_data': json.dumps(chart_data),
            'metadata': log.get_metadata_as_dict()
        })

class Laser2DView(View):
    """Vue pour afficher les données laser 2D"""
    
    def get(self, request, log_id):
        log = get_object_or_404(RobotLog, id=log_id, log_type='LASER2D')
        laser_scan = log.laser_scans.first()
        
        if not laser_scan:
            messages.error(request, 'Aucune donnée laser trouvée pour ce log')
            return redirect('robot_logs:log_detail', log_id)
        
        # Préparer les données pour la visualisation
        range_data = laser_scan.get_range_data_as_list()
        angles = []
        current_angle = laser_scan.angle_min
        for _ in range(len(range_data)):
            angles.append(current_angle)
            current_angle += laser_scan.angle_increment
        
        # Créer des coordonnées cartésiennes pour la visualisation
        points = []
        for angle, distance in zip(angles, range_data):
            # Convertir les coordonnées polaires en coordonnées cartésiennes
            x = distance * np.cos(angle)
            y = distance * np.sin(angle)
            points.append([float(x), float(y)])
        
        visualization_data = {
            'points': points,
            'angle_min': laser_scan.angle_min,
            'angle_max': laser_scan.angle_max,
            'max_range': max(range_data) if range_data else 0,
        }
        
        # Si demandé en JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(visualization_data)
        
        # Sinon, afficher la page
        return render(request, 'robot_logs/laser_view.html', {
            'log': log,
            'laser_scan': laser_scan,
            'visualization_data': json.dumps(visualization_data),
            'metadata': log.get_metadata_as_dict()
        })

class ImageDataView(View):
    """Vue pour afficher les données d'image"""
    
    def get(self, request, log_id):
        log = get_object_or_404(RobotLog, id=log_id, log_type='IMAGE')
        image = log.images.first()
        
        if not image:
            messages.error(request, 'Aucune image trouvée pour ce log')
            return redirect('robot_logs:log_detail', log_id)
        
        # Afficher la page
        return render(request, 'robot_logs/image_view.html', {
            'log': log,
            'image': image,
            'metadata': log.get_metadata_as_dict()
        })

class MDFFileListView(ListView):
    """Vue pour afficher la liste des fichiers MDF importés"""
    
    model = MDFFile
    template_name = 'robot_logs/mdf_file_list.html'
    context_object_name = 'mdf_files'
    paginate_by = 20
    
    def get_queryset(self):
        return super().get_queryset().order_by('-uploaded_at')
