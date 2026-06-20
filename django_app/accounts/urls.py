"""
accounts/urls.py — included from core/urls.py at: path('accounts/', include('accounts.urls'))
Provides app_name='accounts' so templates use {% url 'accounts:login' %} etc.
"""
from django.urls import path  # type: ignore
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect/', views.dashboard_redirect, name='dashboard_redirect'),
]