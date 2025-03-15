from django.db import models
import json

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
    )
    
    timestamp = models.DateTimeField(auto_now_add=False)
    robot_id = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    message = models.TextField()
    source = models.CharField(max_length=200)
    log_type = models.CharField(max_length=10, choices=LOG_TYPES, default='TEXT')
    
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

class MDFFile(models.Model):
    """Modèle pour stocker les fichiers MDF importés"""
    file = models.FileField(upload_to='mdf_files/')
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    mdf_version = models.CharField(max_length=10, null=True, blank=True)
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class DBCFile(models.Model):
    """Modèle pour stocker les fichiers DBC (Database CAN)"""
    file = models.FileField(upload_to='dbc_files/')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class CANMapping(models.Model):
    """Modèle pour associer des canaux CAN dans des fichiers MDF avec des fichiers DBC"""
    mdf_file = models.ForeignKey(MDFFile, on_delete=models.CASCADE, related_name='can_mappings')
    channel_name = models.CharField(max_length=255, help_text="Nom du canal CAN dans le fichier MDF")
    dbc_file = models.ForeignKey(DBCFile, on_delete=models.SET_NULL, null=True, related_name='can_mappings')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('mdf_file', 'channel_name')
        
    def __str__(self):
        return f"{self.channel_name} dans {self.mdf_file.name} -> {self.dbc_file.name if self.dbc_file else 'Aucun DBC'}"
