"""
Module contenant les vues pour la visualisation avancée des courbes.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.http import JsonResponse
import json
import logging

from .models import RobotLog, CurveMeasurement

logger = logging.getLogger(__name__)

class MultiCurveView(View):
    """Vue pour afficher plusieurs courbes simultanément avec des axes Y personnalisables"""
    
    def get(self, request):
        # Récupérer les IDs et configurations des courbes sélectionnées
        curve_configs = request.GET.getlist('curve_config')
        curves_data = []
        selected_logs = []
        
        # Définir des couleurs pour chaque axe Y
        axis_colors = {
            'y1': '#1f77b4',  # bleu
            'y2': '#ff7f0e',  # orange
            'y3': '#2ca02c',  # vert
            'y4': '#d62728'   # rouge
        }
        
        for config in curve_configs:
            # Format attendu: log_id:axis_id (ex: "15:1" pour log_id=15 sur l'axe y1)
            if ':' in config:
                log_id, axis_id = config.split(':')
                try:
                    log = RobotLog.objects.get(id=log_id, log_type='CURVE')
                    selected_logs.append(log)
                    curve_data = log.curve_measurements.all()
                    
                    # Déterminer min et max pour aider à la mise à l'échelle
                    values = [float(data.value) for data in curve_data]
                    min_val = min(values) if values else 0
                    max_val = max(values) if values else 0
                    
                    # Préparer les données pour le graphique
                    timestamps = [data.timestamp.timestamp() * 1000 for data in curve_data]
                    
                    yaxis = f"y{axis_id}"
                    
                    curves_data.append({
                        'id': log_id,
                        'name': log.message,
                        'timestamps': timestamps,
                        'values': values,
                        'sensor_name': curve_data.first().sensor_name if curve_data.exists() else "",
                        'yaxis': yaxis,  # Format pour Plotly: y, y2, y3, etc.
                        'min': min_val,
                        'max': max_val,
                        'metadata': log.get_metadata_as_dict(),
                        'color': axis_colors.get(yaxis, '#1f77b4')
                    })
                except RobotLog.DoesNotExist:
                    continue
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de la courbe {log_id}: {e}")
        
        # Obtenir toutes les courbes disponibles pour la sélection
        available_curves = RobotLog.objects.filter(log_type='CURVE').exclude(
            id__in=[log.id for log in selected_logs]
        ).order_by('-timestamp')
        
        return render(request, 'robot_logs/multi_curve_view.html', {
            'curves_data': json.dumps(curves_data),
            'selected_logs': selected_logs,
            'available_curves': available_curves
        })
