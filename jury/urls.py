from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('home/', views.jury_homepage, name='jury_homepage'),
    path('problem/', views.jury_view_problem, name='jury_problem'),
    path('problem/detail/<problem_id>/', views.jury_problem_detail, name='jury_problem_detail'),
    path('contest/', views.jury_view_contest, name='jury_contest'),
    path('contest/detail/<contest_id>/', views.jury_contest_detail, name='jury_contest_detail'),
    path('team/', views.jury_view_team, name='jury_view_team'),
    path('team/detail/<team_id>/', views.jury_team_detail, name='jury_team_detail'),
    path('user/', views.jury_view_user, name='jury_view_user'),
    path('user/detail/<user_id>/', views.jury_user_detail, name='jury_user_detail'),
    # path('clarification/', views.jury_clarification, name='jury_clarification'),

    # path('scoreboard/refresh/', views.active_contest_scoreboard_refresh, name='active_contest_scoreboard_refresh'),
    # path('submit/refresh/', views.submit, name='active_contest_submit_refresh'),
    # path('scoreboard/admin/', views.view_scoreboard_by_admin, name='view_scoreboard_by_admin'),
    # path('scoreboard/refresh/admin/', views.admin_active_contest_scoreboard_refresh, name='admin_active_contest_scoreboard_refresh'),
    # path('submissions/', views.view_submissions, name='submissions'),
    # path('submit-detail/<int:submit_id>/', views.submission_detail, name='submission_detail'),
    # path('submission/filter/', views.submission_filter, name='submission_filter'),
    # path('specific-problem-submit/', views.specific_problem_submission, name='specific_problem_submission'),
    # path('single-rejudge/<int:submit_id>/', views.single_rejudge, name='single_rejudge'),
    # path('multi-rejudge/<int:problem_id>/<int:user_id>/<user_or_team>/', views.multi_rejudge, name='multi_rejudge'),
    # path('rejudge/process/', views.ajax_rejudge, name='ajax_rejudge'),
    # path('rejudge/', views.all_rejudge, name='rejudge'),

]

