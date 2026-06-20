from django.urls import path
from . import views

app_name = 'admin_insights'

urlpatterns = [
    path('executive-summary/', views.executive_summary, name='executive_summary'),
    path('health-monitor/', views.health_monitor, name='health_monitor'),
    path('anomalies/', views.anomalies, name='anomalies'),
    path('anomalies/<int:anomaly_id>/review/', views.review_anomaly, name='review_anomaly'),
    path('data-quality/', views.data_quality, name='data_quality'),
    
    # API Management URLs
    path('api-management/', views.api_management, name='api_management'),
    path('api-management/partner/create/', views.create_partner, name='create_partner'),
    path('api-management/partner/<uuid:partner_id>/tier/', views.update_partner_tier, name='update_partner_tier'),
    path('api-management/partner/<uuid:partner_id>/deactivate/', views.deactivate_partner, name='deactivate_partner'),
    path('api-management/partner/<uuid:partner_id>/key/generate/', views.generate_api_key, name='generate_api_key'),
    path('api-management/key/<uuid:key_id>/deactivate/', views.deactivate_api_key, name='deactivate_api_key'),
    
    # API Usage, Webhooks, Bulk Import, Celery Monitor URLs
    path('api-usage/', views.api_usage, name='api_usage'),
    path('webhooks/', views.webhooks, name='webhooks'),
    path('bulk-import/', views.bulk_import, name='bulk_import'),
    path('celery-monitor/', views.celery_monitor, name='celery_monitor'),
    path('celery-monitor/task/trigger/', views.trigger_celery_task, name='trigger_celery_task'),
]
