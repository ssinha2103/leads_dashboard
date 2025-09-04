from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('leads/', views.leads_list, name='leads_list'),
    path('leads/export/', views.leads_export, name='leads_export'),
    path('saved-views/save', views.save_view, name='save_view'),
]

