from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('view/', views.contest, name='contest'),
    path('edit/<int:contest_id>/', views.edit_contest, name='edit_contest'),
    path('delete/<int:contest_id>/', views.delete_contest, name='delete_contest'),
    path('delete-done/<int:contest_id>/', views.delete_contest_done, name='delete_contest_done'),
    path('participants/<int:contest_id>/', views.participant, name='participant'),
    path('load-contest/', views.load_contest, name='ajax_load_contest'),
    path('load-contest/admin/', views.load_contest_in_admin, name='ajax_load_contest_admin'),
    path('load-contest/public/', views.load_contest_in_public, name='ajax_load_contest_public'),

    # path('delete-testcase/<int:testcase_id>/', views.delete_testcase, name='delete_testcase'),
    # path('delete-testcase-done/<int:testcase_id>/', views.delete_testcase_done, name='delete_testcase_done'),
    # path('contest/refresh/', views.contest_selector_refresh, name='contest_selector_refresh'),

]
