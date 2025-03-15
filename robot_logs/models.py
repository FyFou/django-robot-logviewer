from django.db import models

class RobotLog(models.Model):
    LOG_LEVELS = (
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    )
    
    timestamp = models.DateTimeField(auto_now_add=False)
    robot_id = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    message = models.TextField()
    source = models.CharField(max_length=200)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.timestamp} - {self.robot_id} - {self.level}: {self.message[:50]}"
