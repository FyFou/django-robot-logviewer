"""
Module contenant les vues pour la visualisation des données CAN.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from django.contrib import messages
import json
import io
import csv
import logging

from .models import RobotLog, CANMessage, CANSignal

logger = logging.getLogger(__name__)

class CANDataView(View):
    """Vue pour afficher les données CAN"""
    
    def get(self, request, log_id):
        """Affiche les données CAN pour un log spécifique"""
        log = get_object_or_404(RobotLog, id=log_id, log_type='CAN')
        
        # Récupérer les messages CAN associés à ce log
        can_messages = log.can_messages.all().prefetch_related('signals')
        
        # Si aucun message, afficher un message d'erreur
        if not can_messages.exists():
            messages.error(request, 'Aucun message CAN trouvé pour ce log')
            return redirect('robot_logs:log_detail', pk=log_id)
        
        # Regrouper les messages par ID/nom pour l'affichage
        grouped_messages = {}
        for message in can_messages:
            key = message.message_name if message.message_name else message.can_id
            if key not in grouped_messages:
                grouped_messages[key] = []
            grouped_messages[key].append(message)
        
        # Limiter le nombre de messages affichés pour des raisons de performance
        display_limit = 100
        total_messages = can_messages.count()
        limited_display = total_messages > display_limit
        
        # Si demandé en JSON (pour des mises à jour AJAX)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Format simplifié pour AJAX
            data = {
                'total_messages': total_messages,
                'message_types': len(grouped_messages),
                'can_ids': list(set(msg.can_id for msg in can_messages[:100]))
            }
            return JsonResponse(data)
        
        # Générer des statistiques sur les messages
        can_id_stats = can_messages.values('can_id').annotate(count=Count('can_id')).order_by('-count')
        can_signal_stats = []
        
        # Collecter les statistiques sur les signaux
        for message in can_messages[:20]:  # Limiter pour la performance
            if message.signals.exists():
                for signal in message.signals.all():
                    can_signal_stats.append({
                        'message_id': message.can_id,
                        'message_name': message.message_name,
                        'signal_name': signal.name,
                        'value': signal.value,
                        'unit': signal.unit
                    })
        
        # Générer un aperçu des données CAN sous forme de graphique
        chart_data = self._generate_chart_data(can_messages[:1000])  # Limiter pour la performance
        
        # Rendu du template
        return render(request, 'robot_logs/can_view.html', {
            'log': log,
            'can_messages': can_messages[:display_limit],
            'grouped_messages': grouped_messages,
            'total_messages': total_messages,
            'limited_display': limited_display,
            'display_limit': display_limit,
            'can_id_stats': can_id_stats[:20],  # Top 20 IDs
            'can_signal_stats': can_signal_stats,
            'metadata': log.get_metadata_as_dict(),
            'chart_data': json.dumps(chart_data) if chart_data else None
        })
    
    def _generate_chart_data(self, can_messages):
        """Génère des données pour un graphique des messages CAN"""
        try:
            # Préparer les données pour le graphique
            from collections import Counter
            import matplotlib.pyplot as plt
            
            # Collecter les identifiants CAN et leurs occurrences
            ids = [msg.can_id for msg in can_messages]
            id_counter = Counter(ids)
            
            if not id_counter:
                return None
            
            # Créer un graphique
            labels = list(id_counter.keys())
            values = list(id_counter.values())
            
            # Trier par fréquence
            sorted_data = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
            labels = [item[0] for item in sorted_data[:15]]  # Top 15 pour lisibilité
            values = [item[1] for item in sorted_data[:15]]
            
            # Format pour Chart.js
            chart_data = {
                'labels': labels,
                'datasets': [{
                    'label': 'Nombre de messages par ID',
                    'data': values,
                    'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }]
            }
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des données du graphique: {e}")
            return None

class CANMessageDetailView(View):
    """Vue pour afficher les détails d'un message CAN spécifique"""
    
    def get(self, request, message_id):
        """Affiche les détails d'un message CAN"""
        message = get_object_or_404(CANMessage, id=message_id)
        signals = message.signals.all()
        
        # Décoder à nouveau le message si un fichier DBC est disponible
        decoded_data = None
        if message.log.log_type == 'CAN' and hasattr(message.log, 'metadata'):
            metadata = message.log.get_metadata_as_dict()
            if 'dbc_file' in metadata:
                try:
                    from .can_parser import DBCParser
                    
                    # Récupérer le fichier DBC
                    dbc_file = None
                    if hasattr(message.log, 'mdf_file') and message.log.mdf_file and message.log.mdf_file.dbc_file:
                        dbc_file = message.log.mdf_file.dbc_file
                    
                    if dbc_file:
                        # Initialiser le parser DBC
                        parser = DBCParser(dbc_file.file.path)
                        
                        # Convertir les données hexadécimales en bytes
                        import binascii
                        data_bytes = binascii.unhexlify(message.raw_data)
                        
                        # Décoder le message
                        message_name, decoded_data = parser.decode_message(message.can_id, data_bytes)
                except Exception as e:
                    logger.error(f"Erreur lors du décodage du message CAN: {e}")
        
        # Afficher la page de détails
        return render(request, 'robot_logs/can_message_detail.html', {
            'message': message,
            'signals': signals,
            'decoded_data': decoded_data,
            'log': message.log
        })

class CANExportView(View):
    """Vue pour exporter les données CAN au format CSV"""
    
    def get(self, request, log_id):
        """Exporte les données CAN au format CSV"""
        log = get_object_or_404(RobotLog, id=log_id, log_type='CAN')
        can_messages = log.can_messages.all().prefetch_related('signals')
        
        # Si aucun message, afficher un message d'erreur
        if not can_messages.exists():
            messages.error(request, 'Aucun message CAN trouvé pour ce log')
            return redirect('robot_logs:log_detail', pk=log_id)
        
        # Créer la réponse HTTP avec un type de contenu CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="can_data_log_{log_id}.csv"'
        
        # Créer le writer CSV
        writer = csv.writer(response)
        
        # Écrire l'en-tête
        writer.writerow(['Timestamp', 'CAN ID', 'Message Name', 'Raw Data', 'Signal Name', 'Signal Value', 'Signal Unit'])
        
        # Écrire les données
        for message in can_messages:
            # Si le message a des signaux, écrire une ligne pour chaque signal
            if message.signals.exists():
                for signal in message.signals.all():
                    writer.writerow([
                        message.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                        message.can_id,
                        message.message_name or '',
                        message.raw_data,
                        signal.name,
                        signal.value,
                        signal.unit or ''
                    ])
            else:
                # Sinon, écrire une ligne pour le message seul
                writer.writerow([
                    message.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                    message.can_id,
                    message.message_name or '',
                    message.raw_data,
                    '', '', ''
                ])
        
        return response

class CANIDFilterView(View):
    """Vue pour filtrer les messages CAN par ID"""
    
    def get(self, request, log_id, can_id):
        """Affiche les messages CAN filtrés par ID"""
        log = get_object_or_404(RobotLog, id=log_id, log_type='CAN')
        
        # Récupérer les messages CAN correspondant à l'ID
        can_messages = log.can_messages.filter(can_id=can_id).prefetch_related('signals')
        
        # Si aucun message, afficher un message d'erreur
        if not can_messages.exists():
            messages.error(request, f'Aucun message CAN trouvé pour l\'ID {can_id}')
            return redirect('robot_logs:can_view', log_id=log_id)
        
        # Limiter le nombre de messages affichés pour des raisons de performance
        display_limit = 500
        total_messages = can_messages.count()
        limited_display = total_messages > display_limit
        
        # Si demandé en JSON (pour des mises à jour AJAX)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Format simplifié pour AJAX
            data = {
                'total_messages': total_messages,
                'can_id': can_id,
                'message_name': can_messages.first().message_name if can_messages.first().message_name else None
            }
            return JsonResponse(data)
        
        # Collecter les informations sur les signaux
        signals_overview = []
        if can_messages.first().signals.exists():
            from collections import defaultdict
            
            # Collecter les valeurs des signaux
            signal_values = defaultdict(list)
            for message in can_messages[:100]:  # Limiter pour la performance
                for signal in message.signals.all():
                    signal_values[signal.name].append({
                        'timestamp': message.timestamp,
                        'value': signal.value,
                        'unit': signal.unit
                    })
            
            # Générer des statistiques sur chaque signal
            for name, values in signal_values.items():
                if values:
                    # Extraire seulement les valeurs numériques
                    numeric_values = [item['value'] for item in values]
                    signals_overview.append({
                        'name': name,
                        'count': len(values),
                        'min': min(numeric_values) if numeric_values else None,
                        'max': max(numeric_values) if numeric_values else None,
                        'unit': values[0]['unit'] if values[0]['unit'] else '',
                        'values': values[:10]  # Limiter pour l'affichage
                    })
        
        # Générer des données pour un graphique des valeurs des signaux
        signal_chart_data = None
        if signals_overview:
            try:
                # Format pour Chart.js
                signal_chart_data = {
                    'datasets': []
                }
                
                # Créer un dataset pour chaque signal
                for signal_info in signals_overview:
                    timestamps = [item['timestamp'].timestamp() * 1000 for item in signal_info['values']]  # En millisecondes pour JS
                    values = [item['value'] for item in signal_info['values']]
                    
                    if timestamps and values:
                        signal_chart_data['datasets'].append({
                            'label': signal_info['name'],
                            'data': [{'x': ts, 'y': val} for ts, val in zip(timestamps, values)],
                            'fill': False
                        })
            except Exception as e:
                logger.error(f"Erreur lors de la génération des données du graphique des signaux: {e}")
        
        # Rendu du template
        return render(request, 'robot_logs/can_id_filter.html', {
            'log': log,
            'can_id': can_id,
            'can_messages': can_messages[:display_limit],
            'total_messages': total_messages,
            'limited_display': limited_display,
            'display_limit': display_limit,
            'message_name': can_messages.first().message_name if can_messages.first().message_name else None,
            'signals_overview': signals_overview,
            'signal_chart_data': json.dumps(signal_chart_data) if signal_chart_data else None
        })
