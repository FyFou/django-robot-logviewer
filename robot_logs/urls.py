from django.urls import path
from . import views

app_name = 'robot_logs'

urlpatterns = [
    path('', views.LogListView.as_view(), name='log_list'),
    path('log/<int:pk>/', views.LogDetailView.as_view(), name='log_detail'),
    path('export-csv/', views.export_logs_csv, name='export_csv'),
]
