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
    path('encuentros/<int:pk>/', views.ver_encuentro, name='ver_encuentro'),
    path('encuentros/nuevo/', views.crear_encuentro, name='crear_encuentro'),
    path('encuentros/editar/<int:pk>/', views.encuentro_form, name='editar_encuentro'),
    path('encuentros/eliminar/<int:pk>/', views.eliminar_encuentro, name='eliminar_encuentro'),
    path('export-db/', views.export_db, name='export_db'),
]
