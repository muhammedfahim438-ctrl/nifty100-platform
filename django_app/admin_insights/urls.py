"""
admin_insights/urls.py
"""
from django.urls import path
from . import views

app_name = 'admin_insights'

urlpatterns = [
    path('executive-summary/', views.executive_summary, name='executive_summary'),
]
