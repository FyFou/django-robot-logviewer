from django.db import models
import json
from django.urls import reverse

class LogGroup(models.Model):
    """Modèle pour regrouper les logs liés à un même événement ou session"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    robot_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    tags = models.CharField(max_length=255, blank=True, null=True, 
                           help_text="Tags séparés par des virgules pour faciliter la recherche")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Groupe de logs"
        verbose_name_plural = "Groupes de logs"
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('robot_logs:log_group_detail', args=[self.id])
    
    def get_log_count(self):
        """Retourne le nombre de logs dans ce groupe"""
        return self.logs.count()
    
    def get_log_types_summary(self):
        """Retourne un résumé des types de logs dans ce groupe"""
        types = self.logs.values_list('log_type', flat=True)
        summary = {}
        for log_type in types:
            if log_type in summary:
                summary[log_type] += 1
            else:
                summary[log_type] = 1
        return summary

class RobotLog(models.Model):
    LOG_LEVELS = (
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    )
    
    LOG_TYPES = (
        ('TEXT', 'Texte'),
        ('CURVE', 'Courbe'),
        ('LASER2D', 'Laser 2D'),
        ('IMAGE', 'Image'),
        ('CAN', 'CAN'),  # Nouveau type pour les données CAN
    )
    
    timestamp = models.DateTimeField(auto_now_add=False)
    robot_id = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    message = models.TextField()
    source = models.CharField(max_length=200)
    log_type = models.CharField(max_length=10, choices=LOG_TYPES, default='TEXT')
    
    # Relation avec un groupe de logs
    group = models.ForeignKey(LogGroup, on_delete=models.SET_NULL, 
                              null=True, blank=True, related_name='logs')
    
    # Champ pour stocker des données associées
    data_file = models.FileField(upload_to='log_data/', null=True, blank=True)
    
    # Pour les métadonnées JSON
    metadata = models.TextField(null=True, blank=True)
    
    def get_metadata_as_dict(self):
        """Convertit les métadonnées JSON en dictionnaire Python"""
        if self.metadata:
            try:
                return json.loads(self.metadata)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_metadata_from_dict(self, metadata_dict):
        """Enregistre un dictionnaire Python comme métadonnées JSON"""
        self.metadata = json.dumps(metadata_dict)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.timestamp} - {self.robot_id} - {self.level}: {self.message[:50]}"

class CurveMeasurement(models.Model):
    log = models.ForeignKey(RobotLog, on_delete=models.CASCADE, related_name='curve_measurements')
    timestamp = models.DateTimeField()
    sensor_name = models.CharField(max_length=100)
    value = models.FloatField()
    
    class Meta:
        ordering = ['timestamp']

class Laser2DScan(models.Model):
    log = models.ForeignKey(RobotLog, on_delete=models.CASCADE, related_name='laser_scans')
    timestamp = models.DateTimeField()
    angle_min = models.FloatField()
    angle_max = models.FloatField()
    angle_increment = models.FloatField()
    range_data = models.TextField()  # Stockage des mesures de distance en JSON
    
    def get_range_data_as_list(self):
        """Convertit les données de plage JSON en liste Python"""
        if self.range_data:
            try:
                return json.loads(self.range_data)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_range_data_from_list(self, range_list):
        """Enregistre une liste Python comme données de plage JSON"""
        self.range_data = json.dumps(range_list)
    
    class Meta:
        ordering = ['timestamp']

class ImageData(models.Model):
    log = models.ForeignKey(RobotLog, on_delete=models.CASCADE, related_name='images')
    timestamp = models.DateTimeField()
    image_file = models.ImageField(upload_to='log_images/')
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    format = models.CharField(max_length=10, default='JPEG')
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return f"Image for {self.log} at {self.timestamp}"

class DBCFile(models.Model):
    """Modèle pour stocker les fichiers DBC (Database CAN)"""
    file = models.FileField(upload_to='dbc_files/')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class CANMessage(models.Model):
    """Modèle pour stocker les messages CAN décodés"""
    log = models.ForeignKey(RobotLog, on_delete=models.CASCADE, related_name='can_messages')
    timestamp = models.DateTimeField()
    can_id = models.CharField(max_length=10)  # ID du message CAN (en hexadécimal)
    message_name = models.CharField(max_length=255, blank=True, null=True)  # Nom du message depuis le DBC
    raw_data = models.CharField(max_length=50)  # Données brutes (hex)
    
    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return f"CAN {self.can_id} at {self.timestamp}"

class CANSignal(models.Model):
    """Modèle pour stocker les signaux extraits des messages CAN"""
    can_message = models.ForeignKey(CANMessage, on_delete=models.CASCADE, related_name='signals')
    name = models.CharField(max_length=255)
    value = models.FloatField()
    unit = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name}: {self.value} {self.unit or ''}"

class MDFFile(models.Model):
    """Modèle pour stocker les fichiers MDF importés"""
    file = models.FileField(upload_to='mdf_files/')
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    mdf_version = models.CharField(max_length=10, null=True, blank=True)
    processed = models.BooleanField(default=False)
    dbc_file = models.ForeignKey(DBCFile, on_delete=models.SET_NULL, null=True, blank=True, related_name='mdf_files')
    
    # Associer automatiquement un groupe pour les logs générés par ce fichier MDF
    log_group = models.ForeignKey(LogGroup, on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='mdf_files')
    
    def __str__(self):
        return self.name
