from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('ver/<int:nroPlaca>/', views.ver, name='ver'),
    path('crear/', views.crear, name='crear'),
    path('editar/<int:nroPlaca>/', views.editar, name='editar'),
    path('eliminar/<int:nroPlaca>/', views.eliminar, name='eliminar'),

    #encuentros
    path('encuentros/', views.listar_encuentros, name='listar_encuentros'),
    path('encuentros/nuevo/', views.crear_encuentro, name='crear_encuentro'),
]
