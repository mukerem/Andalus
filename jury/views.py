from django.shortcuts import render
from problem.models import Problem
from contest.models import Contest
from authentication.models import User, Team
from competitive.models import Submit
from django.contrib.auth.decorators import login_required
from authentication.decorators import jury_auth, jury_auth_and_problem_exist, jury_auth_and_contest_exist, jury_auth_and_team_exist, jury_auth_and_user_exist
# Create your views here.

@login_required
def jury_homepage(request):
    return render(request, 'jury_homepage.html')


@login_required
@jury_auth
def jury_view_problem(request):
    total_problems = Problem.objects.all().order_by('pk').reverse()

    return render(request, 'jury_all_problems.html', {'problem': total_problems})


@login_required
@jury_auth_and_problem_exist
def jury_problem_detail(request, problem_id):
    total_problems = Problem.objects.all().order_by('pk').reverse()
    problem = Problem.objects.get(pk=problem_id)
    return render(request, 'jury_detail_problem.html', {'problem': total_problems,  'this_problem': problem})


@login_required
@jury_auth
def jury_view_contest(request):
    total_contest = Contest.objects.all().order_by('start_time').reverse()

    return render(request, 'jury_all_contests.html', {'contest': total_contest})


@login_required
@jury_auth_and_contest_exist
def jury_contest_detail(request, contest_id):
    total_contest = Contest.objects.all().order_by('start_time').reverse()
    contest = Contest.objects.get(pk=contest_id)
    return render(request, 'jury_detail_contest.html', {'total_contest': total_contest,'this_contest': contest})


@login_required
@jury_auth
def jury_view_team(request):
    total_teams = Team.objects.all().order_by('username')
    return render(request, 'jury_all_teams.html', {'total_teams': total_teams})


@login_required
@jury_auth_and_team_exist
def jury_team_detail(request, team_id):
    total_teams = Team.objects.all().order_by('username')
    team = Team.objects.get(pk=team_id)
    return render(request, 'jury_detail_team.html', {'total_teams': total_teams,'this_team': team})


@login_required
@jury_auth
def jury_view_user(request):
    total_users = User.objects.filter(is_admin=False).order_by('username')
    return render(request, 'jury_all_users.html', {'total_users': total_users})


@login_required
@jury_auth_and_user_exist
def jury_user_detail(request, user_id):
    total_users = User.objects.all().order_by('username')
    this_user = User.objects.get(pk=user_id)
    return render(request, 'jury_detail_user.html', {'total_users': total_users,'this_user': this_user})
