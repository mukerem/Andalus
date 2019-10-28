from django.shortcuts import render, redirect, HttpResponse
from .forms import SendClarification, AdminClarification
from django.contrib.auth.decorators import login_required
from authentication.decorators import team_auth, admin_auth, jury_auth, admin_or_jury_auth
from .models import ClarificationFromUser, ClarificationFromTeam, ClarificationFromAdmin
from django.utils import timezone
from authentication.models import User, Team
from contest.models import Contest
from contest.views import  refresh_active_contest, refresh_active_contest_in_admin
from authentication.views import check_role

# Create your views here.

@login_required
@team_auth
def send_clarification(request):
    refresh_active_contest(request) # refersh the contest session
    all_clarification = None
    form = []
    current_contest_id = request.session.get('contest_741_852_963')
    if current_contest_id:
        current_contest = Contest.objects.get(pk=current_contest_id)
        if 'active_team' in request.session:
            active_team = Team.objects.get(username=request.session.get('active_team'))
            clarification_from = ClarificationFromTeam.objects.filter(team = active_team, contest=current_contest).order_by('send_time')
            clarification_to = ClarificationFromAdmin.objects.filter(team = active_team, contest=current_contest).order_by('send_time')| \
                                ClarificationFromAdmin.objects.filter(is_public = True, contest=current_contest).order_by('send_time')
        else:
            clarification_from = ClarificationFromUser.objects.filter(user = request.user, contest=current_contest).order_by('send_time')
            clarification_to = ClarificationFromAdmin.objects.filter(user = request.user, contest=current_contest).order_by('send_time')| \
                                ClarificationFromAdmin.objects.filter(is_public = True, contest=current_contest).order_by('send_time')

        all_clarification_from = [(i.send_time, i.message, 'from_user') for i in clarification_from]
        all_clarification = [(i.send_time, i.message, 'to_user') for i in clarification_to]
        all_clarification.extend(all_clarification_from)
        all_clarification.sort(reverse=True)

        if request.method == 'POST':
            form = SendClarification(request.POST)
            if form.is_valid():
                message = request.POST.get('message')
                now = timezone.now()
                current_contest = Contest.objects.get(pk=current_contest_id)
                if 'active_team' in request.session:
                    active_team = Team.objects.get(username=request.session.get('active_team'))
                    send = ClarificationFromTeam(message=message, send_time=now, team = active_team, contest=current_contest)
                    send.save()
                else:
                    send = ClarificationFromUser(message=message, send_time=now, user=request.user, contest=current_contest)
                    send.save()
                return redirect('send_clarification')

        else:
            form = SendClarification()
    return render(request, 'view_clarification.html', {'form': form, 'all_clarification': all_clarification})




@login_required
@admin_auth
def clarification_send_by_admin(request):
    refresh_active_contest_in_admin(request) # refersh the contest session
    all_clarification = None
    form = []
    current_contest_id = request.session.get('contest_741_852_963_admin')
    if current_contest_id:
        current_contest = Contest.objects.get(pk=current_contest_id)
        users_list = current_contest.user.all()
        teams_list = current_contest.team.all()
        
        if users_list and teams_list:
            for_all = 'To all Users and Teams'
        elif users_list:
            for_all = 'To all Users'
        elif teams_list:
            for_all = 'To all Teams'
        else:
            for_all = None
        clarification_from_admin = ClarificationFromAdmin.objects.filter(contest=current_contest)
        clarification_from_user = ClarificationFromUser.objects.filter(contest=current_contest)
        clarification_from_team = ClarificationFromTeam.objects.filter(contest=current_contest)

        all_clarification_from_team = [(i.send_time, i.message, 'From Team ' + i.team.username, 'from_team') for i in clarification_from_team]
        all_clarification_from_user = [(i.send_time, i.message, 'From User ' + i.user.username, 'from_user') for i in clarification_from_user]
        all_clarification_to_user = [(i.send_time, i.message, 'To User ' + i.user.username, 'to_user') for i in clarification_from_admin if i.user]
        all_clarification_to_team = [(i.send_time, i.message, 'To Team ' + i.team.username, 'to_team') for i in clarification_from_admin if i.team]
        all_clarification = [(i.send_time, i.message, for_all, 'for_all') for i in clarification_from_admin if i.is_public]

        all_clarification.extend(all_clarification_to_team)
        all_clarification.extend(all_clarification_to_user)
        all_clarification.extend(all_clarification_from_user)
        all_clarification.extend(all_clarification_from_team)
        all_clarification.sort(reverse=True)
        if request.method == 'POST':
            form = AdminClarification(request.POST)
            form.fields['user'].queryset = users_list
            form.fields['team'].queryset = teams_list
            if form.is_valid():
                post = form.save(commit=False)
                now = timezone.now()
                post.send_time = now
                post.contest = current_contest
                post.save()
                return redirect('admin_clarification')

        else:
            form = AdminClarification()
            form.fields['user'].queryset = users_list
            form.fields['team'].queryset = teams_list
    return render(request, 'view_clarification_by_admin.html', {'form': form, 'all_clarification': all_clarification})


@login_required
@admin_or_jury_auth
def all_time_clarifications(request):
    refresh_active_contest_in_admin(request) # refersh the contest session
    all_clarification = None
    
    clarification_from_admin = ClarificationFromAdmin.objects.all()
    clarification_from_user = ClarificationFromUser.objects.all()
    clarification_from_team = ClarificationFromTeam.objects.all()

    all_clarification_from_team = [(i.send_time, i.message, 'From Team ' + i.team.username, 'from_team', i.contest.title) for i in clarification_from_team]
    all_clarification_from_user = [(i.send_time, i.message, 'From User ' + i.user.username, 'from_user', i.contest.title) for i in clarification_from_user]
    all_clarification_to_user = [(i.send_time, i.message, 'To User ' + i.user.username, 'to_user', i.contest.title) for i in clarification_from_admin if i.user]
    all_clarification_to_team = [(i.send_time, i.message, 'To Team ' + i.team.username, 'to_team', i.contest.title) for i in clarification_from_admin if i.team]
    all_clarification = [(i.send_time, i.message, 'To all Teams and Users', 'for_all', i.contest.title) for i in clarification_from_admin if i.is_public]

    all_clarification.extend(all_clarification_to_team)
    all_clarification.extend(all_clarification_to_user)
    all_clarification.extend(all_clarification_from_user)
    all_clarification.extend(all_clarification_from_team)
    all_clarification.sort(reverse=True)
        
    role = check_role(request)
    if role == 'Admin':
        base_page = "admin_base_site.html"
    else:
        base_page = "jury_base.html"
    return render(request, 'all_time_clarifications.html', {'all_clarification': all_clarification, 'base_page': base_page})



@login_required
@jury_auth
def jury_clarification(request):
    all_clarification = None
    clarification_from_admin = ClarificationFromAdmin.objects.all()
    clarification_from_user = ClarificationFromUser.objects.all()
    clarification_from_team = ClarificationFromTeam.objects.all()

    all_clarification_from_team = [(i.send_time, i.message, 'From Team ' + i.team.username, 'from_team', i.contest.title) for i in clarification_from_team]
    all_clarification_from_user = [(i.send_time, i.message, 'From User ' + i.user.username, 'from_user', i.contest.title) for i in clarification_from_user]
    all_clarification_to_user = [(i.send_time, i.message, 'To User ' + i.user.username, 'to_user', i.contest.title) for i in clarification_from_admin if i.user]
    all_clarification_to_team = [(i.send_time, i.message, 'To Team ' + i.team.username, 'to_team', i.contest.title) for i in clarification_from_admin if i.team]
    all_clarification = [(i.send_time, i.message, 'To all Teams and Users', 'for_all', i.contest.title) for i in clarification_from_admin if i.is_public]

    all_clarification.extend(all_clarification_to_team)
    all_clarification.extend(all_clarification_to_user)
    all_clarification.extend(all_clarification_from_user)
    all_clarification.extend(all_clarification_from_team)
    all_clarification.sort(reverse=True)
        
    return render(request, 'jury_clarification.html', {'all_clarification': all_clarification})
