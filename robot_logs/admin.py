from django.contrib import admin
from .models import RobotLog

@admin.register(RobotLog)
class RobotLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'robot_id', 'level', 'short_message', 'source')
    list_filter = ('level', 'robot_id', 'timestamp')
    search_fields = ('message', 'source', 'robot_id')
    date_hierarchy = 'timestamp'
    
    def short_message(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    short_message.short_description = 'Message'
