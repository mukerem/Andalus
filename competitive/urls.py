from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('submit/', views.submit, name='submit'),
    path('problem/', views.active_contest_problem, name='active_contest_problem'),
    path('problems/refresh/', views.active_contest_problem_refresh, name='active_contest_problem_refresh'),
    path('submit/process/', views.ajax_submit_process, name='ajax_submit_process'),
    path('scoreboard/', views.scoreboard, name='scoreboard'),
    path('scoreboard/refresh/', views.scoreboard_refresh, name='scoreboard_refresh'),
    path('scoreboard/public/', views.public_scoreboard, name='public_scoreboard'),
    path('scoreboard/public/refresh/', views.public_scoreboard_refresh, name='public_scoreboard_refresh'),
    path('scoreboard/jury/', views.jury_scoreboard, name='jury_scoreboard'),
    path('scoreboard/jury/refresh/', views.jury_scoreboard_refresh, name='jury_scoreboard_refresh'),
    path('submit/refresh/', views.submit, name='active_contest_submit_refresh'),
    path('submissions/', views.view_submissions, name='submissions'),
    path('submit-detail/<int:submit_id>/', views.submission_detail, name='submission_detail'),
    path('submission/filter/', views.submission_filter, name='submission_filter'),
    path('specific-problem-submit/', views.specific_problem_submission, name='specific_problem_submission'),
    path('single-rejudge/<int:submit_id>/', views.single_rejudge, name='single_rejudge'),
    path('multi-rejudge/<int:problem_id>/<int:user_id>/<user_or_team>/', views.multi_rejudge, name='multi_rejudge'),
    path('rejudge/process/', views.ajax_rejudge, name='ajax_rejudge'),
    path('rejudge/', views.all_rejudge, name='rejudge'),
    path('rescore/process/', views.ajax_rescore, name='ajax_rescore'),
    path('rescore/', views.re_score, name='rescore'),

]

