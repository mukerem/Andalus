from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('send/', views.send_clarification, name='send_clarification'),
    path('view/', views.clarification_send_by_admin, name='admin_clarification'),
    path('view/all-time/', views.all_time_clarifications, name='all_time_clarifications'),

]
