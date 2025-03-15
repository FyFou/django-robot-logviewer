from django.urls import path
from . import views

app_name = 'robot_logs'

urlpatterns = [
    # Vues principales
    path('', views.LogListView.as_view(), name='log_list'),
    path('log/<int:pk>/', views.LogDetailView.as_view(), name='log_detail'),
    path('export-csv/', views.export_logs_csv, name='export_csv'),
    
    # Vues pour les fichiers MDF
    path('import-mdf/', views.ImportMDFView.as_view(), name='import_mdf'),
    path('preview-mdf/', views.PreviewMDFView.as_view(), name='preview_mdf'),
    path('mdf-files/', views.MDFFileListView.as_view(), name='mdf_file_list'),
    
    # Vues pour les types de données spécifiques
    path('log/<int:log_id>/curve/', views.CurveDataView.as_view(), name='curve_view'),
    path('log/<int:log_id>/laser/', views.Laser2DView.as_view(), name='laser_view'),
    path('log/<int:log_id>/image/', views.ImageDataView.as_view(), name='image_view'),
]
