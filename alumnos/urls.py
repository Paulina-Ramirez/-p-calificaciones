from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('calificaciones/', views.calificaciones_view, name='calificaciones'),
    path('logout/', views.logout_view, name='logout'),
]