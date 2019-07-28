from django.shortcuts import render, render_to_response, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from authentication.decorators import admin_auth, admin_auth_and_user_exist, admin_auth_and_team_exist, check_team, admin_or_jury_or_team_auth_and_team_exist, admin_or_jury_auth
from .models import User, Role, Campus, Category, Team, ActiveTeam
from .forms import EditUserProfile, ChangePassword, AddUser, EditMyProfile, CSVUserUpload, TeamRegister, EditTeamProfile, GeneratePassword
from django.contrib import messages
from django.contrib.auth import login, authenticate
from .forms import SignUp
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.db import IntegrityError
from authentication.validators import email_validate, phone_validate
from contest.models import Contest
from contest.views import create_active_contest_session, create_active_contest_session_in_admin, refresh_active_contest, refresh_active_contest_in_admin
import csv


def index(request):
    if request.user.is_authenticated:
        return redirect('andalus_homepage')
    else:
        return redirect('login')


def check_role(request):
    admin = Role.objects.get(short_name='admin')
    team = Role.objects.get(short_name='team')
    jury = Role.objects.get(short_name='jury')
    if request.user.is_admin:
        return 'super_admin'
    elif admin in request.user.role.all():
        return 'Admin'
    elif jury in request.user.role.all():
        return 'Jury'
    elif team in request.user.role.all():
        return 'Team'
    

@login_required
def andalus_homepage(request):
    role = check_role(request)
    if role == 'super_admin':
        return redirect('/admin/')
    elif role == 'Admin':
        create_active_contest_session_in_admin(request)
        return redirect('admin_index')
    elif role == 'Jury':
        create_active_contest_session_in_admin(request)
        return redirect('jury_homepage')
    elif role == 'Team':
        try:
            active_team = ActiveTeam.objects.get(user=request.user).team
        except ActiveTeam.DoesNotExist:
            active_team = None
        if active_team:
            request.session['active_team'] = active_team.username
        create_active_contest_session(request)
        return redirect('submit')
    

@login_required
@admin_auth
def admin_index(request):
    return render(request, 'admin_homepage.html')


@login_required
def my_profile(request):
    if request.user.campus:
        user_campus = request.user.campus.name
    else:
        user_campus = 'None'
    user_category = request.user.category.category
    user_role = ', '.join([i.role for i in request.user.role.all()])
    user_register_date = request.user.register_date
    user_score = request.user.score
    initial_info = {'_campus': user_campus, '_category': user_category, '_role': user_role, '_register_date': user_register_date, '_score': user_score}
    if request.method == "POST":
        form = EditMyProfile(request.POST, request.FILES, instance=request.user, initial=initial_info)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, "The user "+post.username+" was update successfully.")
            redirect('user_view_profile')
    else:
        form = EditMyProfile(instance=request.user, initial=initial_info)

    if '000_555_from_other_role_change_to_team_member' in request.session:
        base_page = "base_site.html"
        refresh_active_contest(request) # refersh the contest session
        role = 'Team'
    else:
        role = check_role(request)
        if role == 'Admin':
            base_page = "admin_base_site.html"
            refresh_active_contest_in_admin(request) # refersh the contest session
        elif role == 'Jury':
            base_page = "jury_base.html"
            refresh_active_contest_in_admin(request) # refersh the contest session
        elif role == 'Judge Host':
            base_page = "judge_host_base.html"
        else:
            base_page = "base_site.html"
            refresh_active_contest(request) # refersh the contest session

    if role == "Team":
        try:
            active_team = ActiveTeam.objects.get(user=request.user).team
        except ActiveTeam.DoesNotExist:
            active_team = None
        team = Team.objects.filter(member=request.user)
    else:
        active_team = None
        team = None
    print(role, active_team, team)
    return render(request, 'profile.html', {'form': form, 'base_page': base_page, 'team': team, 'active_team': active_team})


@login_required
def change_password(request):
    if request.method == "POST":
        form = ChangePassword(request.POST, password=request.user.password)
        if form.is_valid():
            new_password = request.POST.get('new_password')
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, "The password was changed successfully.")
    else:
        form = ChangePassword(password=request.user.password)

    if '000_555_from_other_role_change_to_team_member' in request.session:
        base_page = "base_site.html"
        refresh_active_contest(request) # refersh the contest session
        role = 'Team'
    else:
        role = check_role(request)
        if role == 'Admin':
            base_page = "admin_base_site.html"
            refresh_active_contest_in_admin(request) # refersh the contest session
        elif role == 'Jury':
            base_page = "jury_base.html"
            refresh_active_contest_in_admin(request) # refersh the contest session
        elif role == 'Judge Host':
            base_page = "judge_host_base.html"
        else:
            base_page = "base_site.html"
            refresh_active_contest(request) # refersh the contest session
    return render(request, 'change_password.html', {'form': form,  'base_page': base_page})


@login_required
@check_team
def change_team(request):
    if request.method == 'POST':
        active_team_id = request.POST.get('active_team')
        if active_team_id == '0':
            try:
                active_team = ActiveTeam.objects.get(user=request.user)
                active_team.team = None
                active_team.save()
            except ActiveTeam.DoesNotExist:
                ActiveTeam(user=request.user, team=None).save()
        else:
            select_team = Team.objects.get(pk=active_team_id)
            try:
                active_team = ActiveTeam.objects.get(user=request.user)
                active_team.team = select_team
                active_team.save()
            except ActiveTeam.DoesNotExist:
                ActiveTeam(user=request.user, team=select_team).save()
        try:
            active_team = ActiveTeam.objects.get(user=request.user).team
        except ActiveTeam.DoesNotExist:
            active_team = None
        if active_team:
            request.session['active_team'] = active_team.username
        elif 'active_team' in request.session:
            del request.session['active_team']
        refresh_active_contest(request) # refersh the contest session
        if 'contest_741_852_963' in request.session:
            try:
                contest = Contest.objects.get(pk=request.session.get('contest_741_852_963'))
                contest.last_update = timezone.now()
                contest.save()
            except contest.DoesNotExist:
                pass        
        return redirect('user_view_profile')   
    base_page = "base_site.html"
    team = Team.objects.filter(member=request.user)
    print(team)
    try:
        active = ActiveTeam.objects.get(user=request.user)
    except ActiveTeam.DoesNotExist:
        active = None
    return render(request, 'change_role.html', {'team': team, 'base_page': base_page, 'active': active})


def sign_up(request): 
    if request.method == "POST":
        form = SignUp(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.register_date = timezone.now().date()
            role = Role.objects.get(short_name='team')
            category = Category.objects.get(category='Self Registered')
            post.category = category
            password = request.POST.get('user_password')
            post.set_password(password)
            post.save()
            post.role.set([role])
            # add to active team model if it is participant category and contains team role
            if post.category.category == 'Participant' and Role.objects.get(short_name='team') in post.role.all():
                ActiveTeam(user=post).save()   
            messages.success(request, "signup successfully.")
            user = authenticate(username=post.username, password=password)
            if user is None:
                pass
            else:
                login(request, user)
            return redirect('andalus_homepage')          
    else:
        form = SignUp()
    return render(request, 'sign_up.html', {'form': form})


def validate_data(request, username, first_name, last_name, phone, email, sex, line_number):
    if not username:
        messages.error(request, "invalid username in line " + line_number)
        return 0
    else:
        try:
            User.objects.get(username=username)
            messages.error(request, "username " + username + " was already exists.")
            return 0
        except User.DoesNotExist:
            pass
    if not sex == 'male' and not sex == 'female':
        messages.error(request, "invalid sex for user " + username)
        return 0
    if not first_name:
        messages.error(request, "invalid first_name for user " + username)
        return 0
    if not last_name:
        messages.error(request, "invalid last_name for user " + username)
        return 0
    if phone and not phone_validate(phone):
        messages.error(request, "invalid phone for user " + username)
        return 0
    if not email or not email_validate(email):
        messages.error(request, "invalid email for user " + username)
        return 0
    else:
        try:
            User.objects.get(email=email)
            messages.error(request, "User with this Email already exists.")
            return 0
        except User.DoesNotExist:
            pass
    return 1

    
def user_register_csv(request, csv_file):
    #print(csv_file.content_type)
    if not ( csv_file.content_type == 'text/csv' or csv_file.content_type == 'application/vnd.ms-excel'):
        messages.error(request, "The file is not csv format.")
        return redirect('user')
    else:
        decoded_file = csv_file.read().decode('utf-7').splitlines()
        reader = csv.DictReader(decoded_file)
        line_number = 0
        for row in reader:
            print(row)
            # basic info
            try:
                username = row['username'].strip()
                first_name = row['first_name'].strip()
                last_name = row['last_name'].strip()
                phone = row['phone'].strip().replace("@",'')
                email = row['email'].strip()
                sex = row['sex'].strip()
                role_list = row['role'].split(',')
                campus_short_name = row['campus']
                category_name = row['category']
                print(phone)
            except  KeyError:
                messages.error(request, "invalid column header in csv file.Column headers must be contain username,"
                " first_name, last_name, phone, email, sex, role, category and campus.")
                return redirect('user')

            # validate data
            val = validate_data(request, username, first_name, last_name, phone, email, sex, line_number)
            
            if not val:
                continue
            # role info
            role_set = set()
            for role_name in role_list:
                try:
                    each_role = Role.objects.get(short_name=role_name.strip())
                    role_set.add(each_role)
                except Role.DoesNotExist:
                    messages.error(request, "invalid role list for user " + username)
                    continue

            # category info
            try:
                category = Category.objects.get(category=category_name)
            except Category.DoesNotExist:
                messages.error(request, "invalid category for user " + username)
                continue
            
            # campus info
            if not campus_short_name.replace(' ','') == '':
                try:
                    campus = Campus.objects.get(short_name=campus_short_name)
                except Campus.DoesNotExist:
                    messages.error(request, "invalid campus for user " + username)
                    continue
            else:
                campus = None
            try:
                chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
                if 'password' in row:
                    secret_key = row['password']
                else:
                    secret_key = get_random_string(8, chars)
                obj, created = User.objects.get_or_create(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    email=email,
                    sex=sex,
                    campus=campus,
                    category=category,
                    register_date=timezone.now(),
                )
                obj.role.set(role_set)
                obj.set_password(secret_key)
                obj.save()
                print(obj)
                # add to active team model if it is participant category and contains team role
                if obj.category.category == 'Participant' and Role.objects.get(short_name='team') in obj.role.all():
                    ActiveTeam(user=obj).save()   
            except IntegrityError:
                messages.error(request, "invalid information for user " + username)
            line_number += 1
    if not line_number:
        messages.error(request, " no user register.")
    else:
        messages.success(request, str(line_number ) + " user register successfully.")
    return redirect('user')


@login_required
@admin_auth
def user(request):
    total_users = User.objects.all().exclude(is_admin=True).order_by('username')
 
    if request.method =="POST":
        if 'csv' in request.POST: 
            csv_form = CSVUserUpload(request.POST, request.FILES)
            form = AddUser(campus=request.user.campus)
            #@@@@@@@@@@@@@@@@@@@@@@@@@@
            if csv_form.is_valid():
                file = request.FILES.get('file')
                user_register_csv(request, file)
            #@@@@@@@@@@@@@@@@@@@@@@@@@@
        else:
            csv_form = CSVUserUpload()
            form = AddUser(request.POST, request.FILES, campus=request.user.campus)
            if form.is_valid():
                chars = 'abcdefghijklmnopqrstuvwxyz0123456789@#$%&*'
                secret_key = get_random_string(8, chars)
                post = form.save(commit=False)
                date = timezone.now()
                post.register_date = date
                post.set_password(secret_key)
                post.save()
                form.save_m2m() 
                # add to active team model if it is participant category and contains team role
                if post.category.category == 'Participant' and Role.objects.get(short_name='team') in post.role.all():
                    ActiveTeam(user=post).save()   
                messages.success(request, "user "+post.first_name + ' ' + post.last_name +" was added successfully.")
                redirect('user')
    else:
        csv_form = CSVUserUpload()
        form = AddUser(campus=request.user.campus)
    return render(request, 'all_users.html', {'total_users': total_users, 'form': form, 'csv_form':csv_form})


@login_required
@admin_auth_and_user_exist
def delete_user(request, user_id):
    user = User.objects.get(pk=user_id)
    return render(request, 'delete_user.html', {'this_user': user})


@login_required
@admin_auth_and_user_exist
def delete_user_done(request, user_id):
    user = User.objects.get(pk=user_id)
    user_participated_contest = Contest.objects.filter(user=user)
    for contest in user_participated_contest:
        contest.last_update = timezone.now()
        contest.save()
    user.delete()
    messages.success(request, "user " + user.first_name + ' ' + user.last_name + " was deleted successfully.")
    return redirect('user')


@login_required
@admin_auth_and_user_exist
def edit_user(request, user_id):
    total_users = User.objects.all().exclude(is_admin=True).order_by('username')
    user = User.objects.get(pk=user_id)
    if request.method == "POST":
        form = EditUserProfile(request.POST, instance=user)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            form.save_m2m()
            # add to active team model if it is participant category and contains team role
            try:
                active = ActiveTeam.objects.get(user=post)
                if not post.category.category == 'Participant' or not Role.objects.get(short_name='team') in post.role.all():
                    active.delete() 
            except ActiveTeam.DoesNotExist:
                if post.category.category == 'Participant' and Role.objects.get(short_name='team') in post.role.all():
                    ActiveTeam(user=post).save()
            messages.success(request, "The user "+user.username+" was update successfully.")
            return redirect('edit_user', user.id)
    else:
        form = EditUserProfile(instance=user)
    if user.photo: photo = user.photo.url
    else: photo=None
    return render(request, 'edit_user.html', {'form': form, 'total_users': total_users, 'this_user_id': user.id, 'username': user.username, 'photo': photo})


def generate_users_password_csv(request, total_users):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    writer = csv.writer(response)
    writer.writerow(['#', 'Username', 'Full Name', 'Category', 'Password'])
    for user in total_users:
        writer.writerow(user)
    return response


@login_required
@admin_auth
def generate_user_password(request):
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    if request.method == 'POST':
        form = GeneratePassword(request.POST)
        if form.is_valid():
            category = request.POST.getlist('category')
            total_users = []
            count = 1
            for i in category:
                all_users = User.objects.filter(category__category=i, is_admin=False)
                for user in all_users:
                    secret_key = get_random_string(8, chars)
                    user.set_password(secret_key)
                    user.save()
                    total_users.append((count, user.username, user.first_name + ' ' + user.last_name, user.category, secret_key))
                    count += 1
            excel = generate_users_password_csv(request, total_users)
            return excel  
    else:
        form = GeneratePassword()
    return render(request, 'generate_password.html', {'form': form})


@login_required
@admin_auth
def team(request):
    total_teams = Team.objects.all().order_by('username')
    if request.method =="POST":
        form = TeamRegister(request.POST, campus=request.user.campus)
        if form.is_valid():
            post = form.save(commit=False)
            date = timezone.now()
            post.register_date = date
            post.save()
            form.save_m2m()            
            messages.success(request, "team "+post.username +" was added successfully.")
            redirect('team')
    else:
        form = TeamRegister(campus=request.user.campus)
    return render(request, 'all_teams.html', {'total_teams': total_teams, 'form': form})


@login_required
@admin_auth_and_team_exist
def delete_team(request, team_id):
    team = Team.objects.get(pk=team_id)
    return render(request, 'delete_team.html', {'team': team})


@login_required
@admin_auth_and_team_exist
def delete_team_done(request, team_id):
    team = Team.objects.get(pk=team_id)
    team_participated_contest = Contest.objects.filter(team=team)
    for contest in team_participated_contest:
        contest.last_update = timezone.now()
        contest.save()
    team.delete()
    messages.success(request, "team " + team.username + " was deleted successfully.")
    return redirect('team')


@login_required
@admin_auth_and_team_exist
def edit_team(request, team_id):
    total_teams = Team.objects.all().order_by('username')
    team = Team.objects.get(pk=team_id)
    prevous_users = [i for i in team.member.all()]
    if request.method == "POST":
        form = EditTeamProfile(request.POST, instance=team)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            form.save_m2m()
            messages.success(request, "team " + team.username + " was update successfully.")
            update_users = [i for i in post.member.all()]
            for user in prevous_users:
                if not user in update_users:
                    active_team = ActiveTeam.objects.get(user=user, team=team)
                    active_team.delete()
            if 'active_team' in request.session:
                try:
                    Team.objects.get(username=request.session['active_team'])
                except Team.DoesNotExist:
                    del request.session['active_team']
    else:
        form = EditTeamProfile(instance=team)
    return render(request, 'edit_team.html', {'form': form, 'total_teams': total_teams, 'this_team_id': team.id, 'name': team.username})


@login_required
@admin_or_jury_or_team_auth_and_team_exist
def view_team(request, team_id):
    team = Team.objects.get(pk=team_id)
    if '000_555_from_other_role_change_to_team_member' in request.session:
        base_page = "team_base.html"
        refresh_active_contest(request) # refersh the contest session
        role = 'Team'
    else:
        role = check_role(request)
        if role == 'Admin':
            base_page = "admin_base_site.html"
            refresh_active_contest_in_admin(request) # refersh the contest session
        elif role == 'Jury':
            base_page = "jury_base.html"
            refresh_active_contest_in_admin(request) # refersh the contest session
        else:
            base_page = "team_base.html"
            refresh_active_contest(request) # refersh the contest session
    return render( request, 'view_team.html', {'team': team, 'base_page': base_page})


@login_required
@admin_or_jury_auth
def change_to_team_member(request):
    try:
        active_team = ActiveTeam.objects.get(user=request.user).team
    except ActiveTeam.DoesNotExist:
        active_team = None
    if active_team:
        request.session['active_team'] = active_team.username
    create_active_contest_session(request)
    role = check_role(request)
    request.session['000_555_from_other_role_change_to_team_member'] = role
    if 'contest_741_852_963_admin' in request.session:
        del request.session['contest_741_852_963_admin']
    if 'all_active_contests_741_963_852_admin' in request.session:
        del request.session['all_active_contests_741_963_852_admin']
    return redirect('submit')


@login_required
@admin_or_jury_auth
def change_from_team_member(request):
    if '000_555_from_other_role_change_to_team_member' in request.session:
        del request.session['000_555_from_other_role_change_to_team_member']
    if 'contest_741_852_963' in request.session:
        del request.session['contest_741_852_963']
    if 'all_active_contests_741_963_852' in request.session:
        del request.session['all_active_contests_741_963_852']
    if 'current_contest_end_time' in request.session:
        del request.session['current_contest_end_time']
    if 'current_contest_start_time' in request.session:
        del request.session['current_contest_start_time']

    return redirect('andalus_homepage')


@login_required
@admin_or_jury_auth
def rating(request):
    team_rating = Team.objects.filter(score__gt=0).order_by('score').reverse()
    participant_rating = User.objects.filter(role__short_name='team', category__category="Participant", score__gt=0).order_by('score').reverse()
    observer_rating = User.objects.filter(role__short_name='team', category__category="Observer", score__gt=0).order_by('score').reverse()
    self_registered_rating = User.objects.filter(role__short_name='team', category__category="Self Registered", score__gt=0).order_by('score').reverse()
    system_rating = User.objects.filter(role__short_name='team', category__category="System", score__gt=0).order_by('score').reverse()
    organization_rating = User.objects.filter(role__short_name='team', category__category="Organization", score__gt=0).order_by('score').reverse()

    team = [(rank + 1, row) for rank, row in enumerate(team_rating)]
    participant = [(rank + 1, row) for rank, row in enumerate(participant_rating)]
    observer = [(rank + 1, row) for rank, row in enumerate(observer_rating)]
    self_registered = [(rank + 1, row) for rank, row in enumerate(self_registered_rating)]
    system = [(rank + 1, row) for rank, row in enumerate(system_rating)]
    Organization = [(rank + 1, row) for rank, row in enumerate(organization_rating)]

    role = check_role(request)
    if role == 'Admin':
        base_page = "admin_base_site.html"
    else:
        base_page = "jury_base.html" 
    context = {
        "team": team, 'participant': participant, 'observer': observer, 'self_registered': self_registered, 'system': system,
        'Organization': Organization, 'base_page': base_page
        }
    return render( request, 'rating.html', context) 




