from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('', include('django.contrib.auth.urls')),
    path('admin/index/', views.admin_index, name='admin_index'),
    path('andalus/home', views.andalus_homepage, name='andalus_homepage'),
    path('profile/', views.my_profile, name='user_view_profile'),
    path('sign up/', views.sign_up, name='sign_up'),
    path('profile/password/', views.change_password, name='change_password'),
    path('andalus/', views.andalus_homepage, name='andalus_homepage'),
    path('user/', views.user, name='user'),
    path('user/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('user/delete-done/<int:user_id>/', views.delete_user_done, name='delete_user_done'),
    path('team/', views.team, name='team'),
    path('team/delete/<int:team_id>/', views.delete_team, name='delete_team'),
    path('team/delete-done/<int:team_id>/', views.delete_team_done, name='delete_team_done'),
    path('team/edit/<int:team_id>/', views.edit_team, name='edit_team'),
    path('change_team/', views.change_team, name='change_team'),
    path('view_team/<team_id>/', views.view_team, name='view_team'),
    path('change-to-team-member/', views.change_to_team_member, name='change_to_team_member'),
    path('change-from-team-member/', views.change_from_team_member, name='change_from_team_member'),
    path('user-password/', views.generate_user_password, name='generate_user_password'),
    path('rating/', views.rating, name='rating',)

]
