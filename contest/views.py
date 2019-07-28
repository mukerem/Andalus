from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from authentication.decorators import admin_auth, admin_auth_and_contest_exist, team_auth, admin_or_jury_auth
from .models import Contest
from authentication.models import User, Team
from django.utils import timezone
from .forms import AddContest, EditContest, EditParticipant
from django.contrib import messages
import pytz
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db import IntegrityError
from competitive.models import Rankcache_user_public, Rankcache_team_public, Rankcache_user_jury, Rankcache_team_jury,\
        Scorecache_user_jury, Scorecache_team_jury,Scorecache_user_public, Scorecache_team_public, Submit
# Create your views here.
def time_gap(submit_time, contest_start_time):
    td = submit_time - contest_start_time
    time_taken = td.seconds // 60 + td.days * 3600
    return time_taken

def create_active_contest_session_in_admin(request):
    now = timezone.now()
    all_contests = Contest.objects.filter(active_time__lte=now, deactivate_time__gt=now, enable=True)
    if all_contests:
        request.session['contest_741_852_963_admin'] = str(all_contests[0].pk)
        request.session['all_active_contests_741_963_852_admin'] = [(i.pk, i.short_name) for i in all_contests]
        request.session['current_contest_start_time'] = str(all_contests[0].start_time)
        request.session['current_contest_end_time'] = str(all_contests[0].end_time)
        if len(request.session['all_active_contests_741_963_852_admin']) == 1: 
            request.session['all_active_contests_741_963_852_admin'] = None
    else:
        if 'contest_741_852_963_admin' in request.session:
            del request.session['contest_741_852_963_admin']
        if 'all_active_contests_741_963_852_admin' in request.session:
            del request.session['all_active_contests_741_963_852_admin']


def create_active_contest_session(request):
    now = timezone.now()
    if 'active_team' in request.session:
        active_team = Team.objects.get(username=request.session.get('active_team'))
        all_contests = Contest.objects.filter(team=active_team, active_time__lte=now, deactivate_time__gte=now, enable=True).order_by('title')
    else:
        all_contests = Contest.objects.filter(user=request.user, active_time__lte=now, deactivate_time__gte=now, enable=True).order_by('title')
    if all_contests:
        request.session['contest_741_852_963'] = str(all_contests[0].pk)
        request.session['current_contest_start_time'] = str(all_contests[0].start_time)
        request.session['current_contest_end_time'] = str(all_contests[0].end_time)
        request.session['all_active_contests_741_963_852'] = [(i.pk, i.short_name) for i in all_contests]
        if len(request.session['all_active_contests_741_963_852']) == 1: 
            request.session['all_active_contests_741_963_852'] = None
    else:
        if 'contest_741_852_963' in request.session:
            del request.session['contest_741_852_963']
        if 'all_active_contests_741_963_852' in request.session:
            del request.session['all_active_contests_741_963_852']


def refresh_active_contest_in_admin(request):
    now = timezone.now()
    all_contests = Contest.objects.filter(active_time__lte=now, deactivate_time__gte=now, enable=True)
    if 'contest_741_852_963_admin' in request.session:
        try:
            Contest.objects.get(pk=request.session.get('contest_741_852_963_admin'), active_time__lte=now, deactivate_time__gte=now, enable=True)
        except Contest.DoesNotExist:
            del request.session['contest_741_852_963_admin']
    if 'contest_741_852_963_admin' in request.session:
        try:
            current_contest = Contest.objects.get(pk=request.session.get('contest_741_852_963_admin'))
            request.session['current_contest_start_time'] = str(current_contest.start_time)
            request.session['current_contest_end_time'] = str(current_contest.end_time)
        except Contest.DoesNotExist:
            pass
    else:
        if all_contests:
            request.session['contest_741_852_963_admin'] = all_contests[0].pk
    if all_contests:
        request.session['all_active_contests_741_963_852_admin'] = [(i.pk, i.short_name) for i in all_contests]
        if len(request.session['all_active_contests_741_963_852_admin']) == 1: 
            request.session['all_active_contests_741_963_852_admin'] = None
    elif 'all_active_contests_741_963_852_admin' in request.session:
        del request.session['all_active_contests_741_963_852_admin']


def refresh_active_contest(request):
    now = timezone.now()
    if 'active_team' in request.session:
        active_team = Team.objects.get(username=request.session.get('active_team'))
        all_contests = Contest.objects.filter(team=active_team, active_time__lte=now, deactivate_time__gte=now, enable=True)
    else:
        all_contests = Contest.objects.filter(user=request.user, active_time__lte=now, deactivate_time__gte=now, enable=True)
    if 'contest_741_852_963' in request.session:
        try:
            if 'active_team' in request.session:
                active_team = Team.objects.get(username=request.session.get('active_team'))
                Contest.objects.get(pk=request.session.get('contest_741_852_963'), team=active_team, active_time__lte=now, deactivate_time__gte=now, enable=True)
            else:
                Contest.objects.get(pk=request.session.get('contest_741_852_963'), user=request.user, active_time__lte=now, deactivate_time__gte=now, enable=True)
        except Contest.DoesNotExist:
            del request.session['contest_741_852_963']
    if 'contest_741_852_963' in request.session:
        pass
    else:
        if all_contests:
            request.session['contest_741_852_963'] = all_contests[0].pk
    if 'contest_741_852_963' in request.session:
        try:
            current_contest = Contest.objects.get(pk=request.session.get('contest_741_852_963'))
            request.session['current_contest_start_time'] = str(current_contest.start_time)
            request.session['current_contest_end_time'] = str(current_contest.end_time)
        except Contest.DoesNotExist:
            pass
    if all_contests:
        request.session['all_active_contests_741_963_852'] = [(i.pk, i.short_name) for i in all_contests]
        if len(request.session['all_active_contests_741_963_852']) == 1: 
            request.session['all_active_contests_741_963_852'] = None
    elif 'all_active_contests_741_963_852' in request.session:
        del request.session['all_active_contests_741_963_852']



def refresh_active_contest_public(request):
    now = timezone.now()
    all_contests = Contest.objects.filter(active_time__lte=now, deactivate_time__gte=now, enable=True)
    if 'public_contest_741_852_963' in request.session:
        try:
            Contest.objects.get(pk=request.session.get('public_contest_741_852_963'), active_time__lte=now, deactivate_time__gte=now, enable=True)
        except Contest.DoesNotExist:
            del request.session['public_contest_741_852_963']
    if 'public_contest_741_852_963' in request.session:
        pass
    else:
        if all_contests:
            request.session['public_contest_741_852_963'] = all_contests[0].pk
    if 'public_contest_741_852_963' in request.session:
        try:
            current_contest = Contest.objects.get(pk=request.session.get('public_contest_741_852_963'))
            request.session['current_contest_start_time'] = str(current_contest.start_time)
            request.session['current_contest_end_time'] = str(current_contest.end_time)
        except Contest.DoesNotExist:
            pass
    if all_contests:
        request.session['all_public_contest_741_852_963'] = [(i.pk, i.short_name) for i in all_contests]
        if len(request.session['all_public_contest_741_852_963']) == 1: 
            request.session['all_public_contest_741_852_963'] = None
    elif 'all_public_contest_741_852_963' in request.session:
        del request.session['all_public_contest_741_852_963']
           

@login_required
@admin_auth
def contest(request):
    total_contest = Contest.objects.all().order_by('start_time').reverse()
    if request.method =="POST":
        form = AddContest(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            form.save_m2m() 
            if request.POST.get('is_public'):
                post.user.set([i for i in User.objects.filter(role__role='Team Member')])
                post.team.set([i for i in Team.objects.all()])
                form.save_m2m() 
                for users in post.user.all():
                    jury = Rankcache_user_jury(contest=post, user=users)
                    jury.save()
                    public = Rankcache_user_public(contest=post, user=users)
                    public.save()
                for teams in post.team.all():
                    jury = Rankcache_team_jury(contest=post, team=teams)
                    jury.save()
                    public = Rankcache_team_public(contest=post, team=teams)
                    public.save()
                messages.success(request, "contest "+post.title+" was added successfully.")
                refresh_active_contest_in_admin(request)
                refresh_active_contest_public(request)
                redirect('contest')
            else:
                return redirect('participant',post.pk)
    else:
        form = AddContest()
    return render(request, 'all_contest.html', {'contest': total_contest, 'form': form})


@login_required
@admin_auth_and_contest_exist
def delete_contest(request, contest_id):
    contest = Contest.objects.get(pk=contest_id)
    return render(request, 'delete_contest.html', {'contest': contest})


@login_required
@admin_auth_and_contest_exist
def delete_contest_done(request, contest_id):
    contest = Contest.objects.get(pk=contest_id)
    contest.delete()
    messages.success(request, "The contest " + contest.title + " was deleted successfully.")
    refresh_active_contest_in_admin(request)
    refresh_active_contest_public(request)
    return redirect('contest')


def team_score_and_rank(contest, problem, active_team, result, submit):
    if submit.submit_time > contest.end_time:
        return
    point = submit.problem.point
    try:
        rank_cache_jury = Rankcache_team_jury.objects.get(team=active_team, contest=contest)
    except Rankcache_team_jury.DoesNotExist:
        raise PermissionDenied
    try:
        score_cache_jury = Scorecache_team_jury.objects.get(rank_cache=rank_cache_jury, problem=problem)
    except Scorecache_team_jury.DoesNotExist:
        score_cache_jury = Scorecache_team_jury(rank_cache=rank_cache_jury, problem=problem)
        score_cache_jury.save()
    if score_cache_jury.is_correct:
        return
    if result == "Correct":
        score_cache_jury.is_correct = True
        score_cache_jury.correct_submit_time = submit.submit_time
        rank_cache_jury.point += point
        rank_cache_jury.punish_time += 20 * score_cache_jury.punish + time_gap(score_cache_jury.correct_submit_time, contest.start_time)
        rank_cache_jury.save()
    elif not result == "Compiler Error":
        score_cache_jury.punish += 1
    score_cache_jury.submission += 1
    score_cache_jury.save()
    try:
        rank_cache_public = Rankcache_team_public.objects.get(team=active_team, contest=contest)
    except Rankcache_team_public.DoesNotExist:
        raise PermissionDenied
    try:
        score_cache_public = Scorecache_team_public.objects.get(rank_cache=rank_cache_public, problem=problem)
    except Scorecache_team_public.DoesNotExist:
        score_cache_public = Scorecache_team_public(rank_cache=rank_cache_public, problem=problem)
        score_cache_public.save()
    if score_cache_public.is_correct:
        return
    if contest.frozen_time and contest.unfrozen_time and contest.frozen_time <= submit.submit_time and submit.submit_time < contest.unfrozen_time:
        score_cache_public.pending += 1
        score_cache_public.save()
    elif contest.start_time <= submit.submit_time and submit.submit_time < contest.end_time:
        score_cache_public.is_correct = score_cache_jury.is_correct
        score_cache_public.correct_submit_time = score_cache_jury.correct_submit_time
        score_cache_public.punish = score_cache_jury.punish
        score_cache_public.submission = score_cache_jury.submission
        score_cache_public.save()
        rank_cache_public.point = rank_cache_jury.point
        rank_cache_public.punish_time = rank_cache_jury.punish_time
        rank_cache_public.save()


def user_score_and_rank(contest, problem, user, result, submit):
    if submit.submit_time > contest.end_time:
        return
    point = submit.problem.point
    try:
        rank_cache_jury = Rankcache_user_jury.objects.get(user=user, contest=contest)
    except Rankcache_user_jury.DoesNotExist:
        raise PermissionDenied
    try:
        score_cache_jury = Scorecache_user_jury.objects.get(rank_cache=rank_cache_jury, problem=problem)
    except Scorecache_user_jury.DoesNotExist:
        score_cache_jury = Scorecache_user_jury(rank_cache=rank_cache_jury, problem=problem)
        score_cache_jury.save()
    if score_cache_jury.is_correct:
        return
    if result == "Correct":
        score_cache_jury.is_correct = True
        score_cache_jury.correct_submit_time = submit.submit_time
        rank_cache_jury.point += 1
        rank_cache_jury.punish_time += 20 * score_cache_jury.punish + time_gap(score_cache_jury.correct_submit_time, contest.start_time)
        rank_cache_jury.save()
    elif not result == "Compiler Error":
        score_cache_jury.punish += point
    score_cache_jury.submission += 1
    score_cache_jury.save()
    try:
        rank_cache_public = Rankcache_user_public.objects.get(user=user, contest=contest)
    except Rankcache_user_public.DoesNotExist:
        raise PermissionDenied
    try:
        score_cache_public = Scorecache_user_public.objects.get(rank_cache=rank_cache_public, problem=problem)
    except Scorecache_user_public.DoesNotExist:
        score_cache_public = Scorecache_user_public(rank_cache=rank_cache_public, problem=problem)
        score_cache_public.save()
    if score_cache_public.is_correct:
        return
    if contest.frozen_time and contest.unfrozen_time and contest.frozen_time <= submit.submit_time and submit.submit_time < contest.unfrozen_time:
        score_cache_public.pending += 1
        score_cache_public.submission += 1
        score_cache_public.save()
    elif contest.start_time <= submit.submit_time and submit.submit_time < contest.end_time:
        score_cache_public.is_correct = score_cache_jury.is_correct
        score_cache_public.correct_submit_time = score_cache_jury.correct_submit_time
        score_cache_public.punish = score_cache_jury.punish
        score_cache_public.submission = score_cache_jury.submission
        score_cache_public.save()
        rank_cache_public.point = rank_cache_jury.point
        rank_cache_public.punish_time = rank_cache_jury.punish_time
        rank_cache_public.save()


def update_rank_score(current_contest, previous_start_time, previous_end_time, previous_frozen_time, previous_unfrozen_time):
    # if previous_start_time == current_contest.start_time and previous_end_time == current_contest.end_time and \
    #     previous_frozen_time == current_contest.frozen_time and previous_unfrozen_time == current_contest.unfrozen_time:
    #     return 
    user_public_rank_cache = Rankcache_user_public.objects.filter(contest=current_contest)
    for rank in user_public_rank_cache:
        rank.point = 0
        rank.punish_time = 0
        rank.save()
    user_jury_rank_cache = Rankcache_user_jury.objects.filter(contest=current_contest)
    for rank in user_jury_rank_cache:
        rank.point = 0
        rank.punish_time = 0
        rank.save()
    team_public_rank_cache = Rankcache_team_public.objects.filter(contest=current_contest)
    for rank in team_public_rank_cache:
        rank.point = 0
        rank.punish_time = 0
        rank.save()
    team_jury_rank_cache = Rankcache_team_jury.objects.filter(contest=current_contest)
    for rank in team_jury_rank_cache:
        rank.point = 0
        rank.punish_time = 0
        rank.save()

    q = Q(problem=None)
    for pro in current_contest.problem.all():
        q = q | Q(problem=pro)

    qq = Q(user=None)
    for user in current_contest.user.all():
        qq = qq | Q(user=user)
        
    qqq = Q(team=None)
    for team in current_contest.team.all():
        qqq = qqq | Q(team=team)
        
    user_public_score_cache = Scorecache_user_public.objects.filter(q, rank_cache__contest=current_contest)
    for score in user_public_score_cache:
        score.delete()
    user_jury_score_cache = Scorecache_user_jury.objects.filter(q, rank_cache__contest=current_contest)
    for score in user_jury_score_cache:
        score.delete()
    team_public_score_cache = Scorecache_team_public.objects.filter(q, rank_cache__contest=current_contest)
    for score in team_public_score_cache:
        score.delete()
    team_jury_score_cache = Scorecache_team_jury.objects.filter(q, rank_cache__contest=current_contest)
    for score in team_jury_score_cache:
        score.delete()

    all_team_submit = Submit.objects.filter(q, qqq, contest=current_contest, submit_time__gte=current_contest.start_time,
                                            submit_time__lte=current_contest.end_time).exclude(team=None).exclude(result='').order_by('submit_time')
    all_user_submit = Submit.objects.filter(q, qq, contest=current_contest, submit_time__gte=current_contest.start_time,
                                            submit_time__lte=current_contest.end_time, team=None).exclude(result='').order_by('submit_time')
    for submit in all_team_submit:
        team_score_and_rank(current_contest, submit.problem, submit.team, submit.result, submit)
    for submit in all_user_submit:
        user_score_and_rank(current_contest, submit.problem, submit.user, submit.result, submit)
     

@login_required
@admin_auth_and_contest_exist
def edit_contest(request, contest_id):
    contest = Contest.objects.get(pk=contest_id)
    previous_start_time = contest.start_time
    previous_end_time = contest.end_time
    previous_frozen_time = contest.frozen_time
    previous_unfrozen_time = contest.unfrozen_time
    if request.method == "POST":
        form = EditContest(request.POST, request.FILES,instance=contest)
        if form.is_valid():
            previous_problems = [i for i in contest.problem.all()]
            post = form.save(commit=False)
            post.last_update = timezone.now()
            post.save()
            form.save_m2m()
            if request.POST.get('is_public'):
                post.user.set([i for i in User.objects.filter(role__role='Team Member')])
                post.team.set([i for i in Team.objects.all()])
                for users in post.user.all():
                    try:
                        jury = Rankcache_user_jury(contest=post, user=users)
                        jury.save()
                    except IntegrityError:
                        pass
                    try:
                        public = Rankcache_user_public(contest=post, user=users)
                        public.save()
                    except IntegrityError:
                        pass
                for teams in post.team.all():
                    try:
                        jury = Rankcache_team_jury(contest=post, team=teams)
                        jury.save()
                    except IntegrityError:
                        pass
                    try:
                        public = Rankcache_team_public(contest=post, team=teams)
                        public.save()
                    except IntegrityError:
                        pass
            
            messages.success(request, "The contest "+contest.title+" was update successfully.")
            refresh_active_contest_in_admin(request)
            refresh_active_contest_public(request)
            update_rank_score(contest, previous_start_time, previous_end_time, previous_frozen_time, previous_unfrozen_time)
            # redirect('edit_contest/'+str(contest_id)+'/')
    else:
        form = EditContest(instance=contest)
    if contest.photo: photo = contest.photo.url
    else: photo=None
    total_contests = Contest.objects.all().order_by('start_time').reverse()
    return render(request, 'edit_contest.html', {'form': form, 'total_contests': total_contests, 'this_contest_id': contest.id,
        'title': contest.title, 'photo': photo})
       

@login_required
@admin_auth_and_contest_exist
def participant(request, contest_id):
    contest = Contest.objects.get(pk=contest_id)
    if request.method == "POST":
        form = EditParticipant(request.POST, contest=contest)
        if form.is_valid():
            if contest.is_public:
                contest.user.set([i for i in User.objects.filter(role__short_name='team')])
                contest.team.set([i for i in Team.objects.all()])
                messages.success(request, "The contest "+contest.title+" was update successfully.")
                contest.save()
                return redirect('edit_contest',contest_id)
            user_list = set()
            team_list = set()
            team = request.POST.getlist('team')
            particip = request.POST.getlist('participant')
            _self = request.POST.getlist('self_registered')
            observer = request.POST.getlist('observer')
            system = request.POST.getlist('system')
            org = request.POST.getlist('organization')
            for i in team:
                try:
                    _t = Team.objects.get(pk=i)
                except Team.DoesNotExist:
                    raise Http404("team with pk " + i + " was not registered")
                team_list.add(_t)
            for i in particip:
                try:
                    _u = User.objects.get(pk=i)
                except User.DoesNotExist:
                    raise Http404("user with pk " + i + " was not registered")
                user_list.add(_u)
            for i in _self:
                try:
                    _u = User.objects.get(pk=i)
                except User.DoesNotExist:
                    raise Http404("user with pk " + i + " was not registered")
                user_list.add(_u)
            for i in observer:
                try:
                    _u = User.objects.get(pk=i)
                except User.DoesNotExist:
                    raise Http404("user with pk " + i + " was not registered")
                user_list.add(_u)
            for i in system:
                try:
                    _u = User.objects.get(pk=i)
                except User.DoesNotExist:
                    raise Http404("user with pk " + i + " was not registered")
                user_list.add(_u)
            for i in org:
                try:
                    _u = User.objects.get(pk=i)
                except User.DoesNotExist:
                    raise Http404("user with pk " + i + " was not registered")
                user_list.add(_u)
            contest.team.set(team_list)
            contest.user.set(user_list)
            contest.last_update = timezone.now()
            contest.save()
            contest_users = contest.user.all()
            contest_teams = contest.team.all()
            for users in contest_users:
                    try:
                        jury = Rankcache_user_jury(contest=contest, user=users)
                        jury.save()
                    except IntegrityError:
                        pass
                    try:
                        public = Rankcache_user_public(contest=contest, user=users)
                        public.save()
                    except IntegrityError:
                        pass
            for teams in contest_teams:
                try:
                    jury = Rankcache_team_jury(contest=contest, team=teams)
                    jury.save()
                except IntegrityError:
                    pass
                try:
                    public = Rankcache_team_public(contest=contest, team=teams)
                    public.save()
                except IntegrityError:
                    pass
            cache_public_users = Rankcache_user_public.objects.filter(contest=contest)
            cache_jury_users = Rankcache_user_jury.objects.filter(contest=contest)
            cache_public_teams = Rankcache_team_public.objects.filter(contest=contest)
            cache_jury_teams = Rankcache_team_jury.objects.filter(contest=contest)
            for users in cache_public_users: 
                if not users.user in contest_users:
                    users.delete()
            for users in cache_jury_users: 
                if not users.user in contest_users:
                    users.delete()
            for teams in cache_public_teams: 
                if not teams.team in contest_teams:
                    teams.delete()
            for teams in cache_jury_teams: 
                if not teams.team in contest_teams:
                    teams.delete()
            messages.success(request, "The contest "+contest.title+" was update successfully.")
            return redirect('edit_contest',contest_id)
    else:
        form = EditParticipant(contest=contest)
    return render(request, 'participants.html', {'form': form, 'this_contest_id': contest.id, 'title': contest.title})
       

@login_required
@team_auth
def load_contest(request): 
    refresh_active_contest(request) # refersh the contest session
    contest_id = request.GET.get('code')
    request.session['contest_741_852_963'] = contest_id
    current_contest = Contest.objects.get(pk=contest_id)
    request.session['current_contest_start_time'] = str(current_contest.start_time)
    request.session['current_contest_end_time'] = str(current_contest.end_time)
    return HttpResponse('')



@login_required
@admin_or_jury_auth
def load_contest_in_admin(request):
    refresh_active_contest_in_admin(request) # refersh the contest session
    contest_id = request.GET.get('code')
    request.session['contest_741_852_963_admin'] = contest_id
    print(contest_id)
    return HttpResponse('')


def load_contest_in_public(request):
    refresh_active_contest_public(request) # refersh the contest session
    contest_id = request.GET.get('code')
    request.session['public_contest_741_852_963'] = contest_id
    current_contest = Contest.objects.get(pk=contest_id)
    request.session['current_contest_start_time'] = str(current_contest.start_time)
    request.session['current_contest_end_time'] = str(current_contest.end_time)
    return HttpResponse('')

