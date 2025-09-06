from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()
router.register(r'emails', views.EmailViewSet)
router.register(r'stats', views.DailyStatsViewSet)
router.register(r'dashboard', views.DashboardViewSet, basename='dashboard')

app_name = 'emailbot'

urlpatterns = [
    # Web dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
