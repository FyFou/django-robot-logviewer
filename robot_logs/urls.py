from django.urls import path
from . import views
from . import views_dbc
from . import views_can
from . import views_curve
from . import views_group

app_name = 'robot_logs'

urlpatterns = [
    # Vues principales - changement pour mettre les groupes en page principale
    path('', views_group.LogGroupListView.as_view(), name='home'),  # Nouvelle URL principale
    path('logs/', views.LogListView.as_view(), name='log_list'),    # Logs individuels maintenant sous /logs/
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
    
    # Vues pour les courbes avancées
    path('curves/compare/', views_curve.MultiCurveView.as_view(), name='multi_curve_view'),
    
    # Vues pour les fichiers DBC
    path('dbc-files/', views_dbc.DBCFileListView.as_view(), name='dbc_file_list'),
    path('dbc-files/upload/', views_dbc.DBCFileUploadView.as_view(), name='dbc_file_upload'),
    path('dbc-files/<int:pk>/', views_dbc.DBCFileDetailView.as_view(), name='dbc_file_detail'),
    path('dbc-files/<int:pk>/delete/', views_dbc.DBCFileDeleteView.as_view(), name='dbc_file_delete'),
    
    # Vues pour les données CAN
    path('log/<int:log_id>/can/', views_can.CANDataView.as_view(), name='can_view'),
    path('log/<int:log_id>/can/export/', views_can.CANExportView.as_view(), name='can_export'),
    path('can-message/<int:message_id>/', views_can.CANMessageDetailView.as_view(), name='can_message_detail'),
    path('log/<int:log_id>/can/filter/<str:can_id>/', views_can.CANIDFilterView.as_view(), name='can_id_filter'),
    
    # Vues pour les groupes de logs
    path('groups/', views_group.LogGroupListView.as_view(), name='log_group_list'),  # Gardé pour compatibilité
    path('groups/create/', views_group.LogGroupCreateView.as_view(), name='log_group_create'),
    path('groups/<int:pk>/', views_group.LogGroupDetailView.as_view(), name='log_group_detail'),
    path('groups/<int:pk>/update/', views_group.LogGroupUpdateView.as_view(), name='log_group_update'),
    path('groups/<int:pk>/delete/', views_group.LogGroupDeleteView.as_view(), name='log_group_delete'),
    path('groups/assign-logs/', views_group.AssignLogsToGroupView.as_view(), name='assign_logs_to_group'),
    path('groups/<int:group_id>/remove-logs/', views_group.RemoveLogsFromGroupView.as_view(), name='remove_logs_from_group'),
    path('groups/merge/', views_group.MergeLGroupsView.as_view(), name='merge_groups'),
]
