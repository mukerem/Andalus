from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from authentication.decorators import team_auth, admin_auth, admin_auth_and_submit_exist, admin_or_jury_auth, admin_or_jury_auth_and_submit_exist
from django.db import IntegrityError
from django.core.files import File
from contest.models import Contest
from django.utils import timezone
from django.contrib import messages
from .forms import SubmitAnswer
from .models import Language, Submit, Testcase_Output
from problem.models import TestCase, Problem
from authentication.models import Team, User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
import os
import time
import json
import subprocess
import sys
from threading import Timer
from contest.views import create_active_contest_session, create_active_contest_session_in_admin, refresh_active_contest, refresh_active_contest_in_admin, refresh_active_contest_public
from authentication.views import check_role
from competitive.models import Rankcache_user_public, Rankcache_team_public, Rankcache_user_jury, Rankcache_team_jury,\
        Scorecache_user_jury, Scorecache_team_jury,Scorecache_user_public, Scorecache_team_public
from contest.views import user_score_and_rank, team_score_and_rank


def time_gap(submit_time, contest_start_time):
    td = submit_time - contest_start_time
    time_taken = td.seconds // 60 + td.days * 3600
    return time_taken


def calculate_problem_score_public(score_cache_jury, total_problems, contest_start_time):
    score_vs_problem = dict()
    for score in score_cache_jury:
        pro = score.problem
        if score.is_correct:
            time = time_gap(score.correct_submit_time, contest_start_time)
            score_vs_problem[pro] = (score.submission, time, "#32cd32")
        else:
            score_vs_problem[pro] = (score.submission, -1, "#cd5c5c")
    problem_display = []
    for pro in total_problems:
        if pro in score_vs_problem:
            problem_display.append(score_vs_problem[pro])
        else:
            problem_display.append((0,-1, "#ffffff"))
    return problem_display


def my_score(request, contest_id):
    current_contest = Contest.objects.get(pk=contest_id)
    contest_start_time = current_contest.start_time
    total_problems = current_contest.problem.all().order_by('short_name')
    if 'active_team' in request.session:
        active_team = Team.objects.get(username=request.session.get('active_team'))
        rank_cache_jury = Rankcache_team_jury.objects.get(team=active_team, contest=current_contest)
        score_cache_jury = Scorecache_team_jury.objects.filter(rank_cache=rank_cache_jury)
    else:
        rank_cache_jury = Rankcache_user_jury.objects.get(user=request.user, contest=current_contest)
        score_cache_jury = Scorecache_user_jury.objects.filter(rank_cache=rank_cache_jury)
    problem_display = calculate_problem_score_public(score_cache_jury, total_problems, contest_start_time)
    my_point = float(rank_cache_jury.point)
    if my_point == int(my_point): my_point = int(my_point)
    my_punish_time = rank_cache_jury.punish_time
    display = [my_point, my_punish_time, problem_display]
    return display


def convert_to_command(file_name, filename_without_extension, command):
    command = command.replace('<', '')
    command = command.replace('>', '')
    command = command.replace('#', filename_without_extension)
    command = command.replace('@', file_name)
    return command


def check_answer(correct_answer_file, user_answer_file):
    correct_answer = open(correct_answer_file, 'r')
    user_answer = open(user_answer_file, 'r')
    correct_answer_list = []
    user_answer_list = []
    for j in correct_answer:
        x = j.rstrip()
        if x:
            correct_answer_list.append(x)
    for j in user_answer:
        x = j.rstrip()
        if x:
            user_answer_list.append(x)
    correct_answer.close()
    user_answer.close()
    if correct_answer_list and not user_answer_list:
        return 'No Output'
    elif correct_answer_list == user_answer_list:
        return 'Correct'
    else:
        return 'Wrong Answer'
        

def run(command, input_file_path, output_file_path, time_limit_bound):
    cmd = command+ "<" + input_file_path +">" + output_file_path
    proc = subprocess.Popen(cmd, shell=True)
    timer = Timer(time_limit_bound, proc.kill)
    timer.start()
    start_time = time.clock()
    proc.communicate()
    end_time = time.clock()
    if timer.is_alive():
        timer.cancel()
        if proc.returncode:
            return ("Run Time Error", 0.0)
        else:
            return ('Correct', end_time - start_time)
    return ('Time Limit Exceeded', time_limit_bound)


def compile(command):
    failure = subprocess.call(command, shell=True)
    if failure:
        return False
    return True


def judge(file_name, problem, language, submit, rejudge=False):
    if not os.path.exists(file_name):
        raise PermissionDenied
    without_extension = file_name
    try:
        index = without_extension[::-1].index('.')
        try:
            slash_index = without_extension[::-1].index('/')
            if index < slash_index:
                without_extension = without_extension[::-1][index+1:][::-1]
        except Exception:
            without_extension = without_extension[::-1][index+1:][::-1]
    except Exception:
        pass
    compile_command = language.compile_command
    run_command = language.run_command
    new_compile_command = convert_to_command(file_name=file_name, command=compile_command, filename_without_extension=without_extension) 
    new_run_command = convert_to_command(file_name=file_name, command=run_command, filename_without_extension=without_extension) 
    if language.name == 'Java':
        new_run_command = (new_run_command[::-1].replace('/', ' ', 1))[::-1]
    result = compile(command=new_compile_command)
    if not result:
        return 'Compiler Error'
    test_cases = [i for i in TestCase.objects.filter(problem=problem).order_by('name')]
    time_limit = float(problem.time_limit)
    memory_limit = float('inf')
    if problem.memory_limit:
        memory_limit = problem.memory_limit
    submit_result = "Correct"
    for each in test_cases:
        input_file = each.input
        output_file = each.output
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        user_output_text_path = os.path.join(BASE_DIR, 'static/user_output.txt')
        if rejudge:
            try:
                insert = Testcase_Output.objects.get(submit=submit, test_case=each) # for all except compiler error and run time error
            except Testcase_Output.DoesNotExist:
                try:
                    user_output = File(open(user_output_text_path, 'r'))
                    insert = Testcase_Output(output_file=user_output, test_case=each, submit=submit)
                    insert.save()
                except IntegrityError:
                    pass
        else:
            try:

                user_output = File(open(user_output_text_path, 'r'))
                insert = Testcase_Output(output_file=user_output, test_case=each, submit=submit)
                insert.save()
            except IntegrityError:
                pass
        testcase_input_file_path = input_file.path
        user_output_file_path = insert.output_file.path
        testcase_output_file_path = output_file.path
        result, execute_time = run(command=new_run_command, input_file_path = testcase_input_file_path, output_file_path = user_output_file_path, time_limit_bound=time_limit)
        insert.execution_time = execute_time
        if result == "Run Time Error":
            insert.result = "Run Time Error"
            insert.save()
            return "Run Time Error"
        elif result == 'Time Limit Exceeded':
            insert.result = 'Time Limit Exceeded'
            insert.save()
            return 'Time Limit Exceeded'
        result = check_answer(correct_answer_file=testcase_output_file_path, user_answer_file=user_output_file_path)
        insert.result = result
        insert.save()
        if result == 'Correct':
            continue
        elif result == "Wrong Answer" :
            submit_result = "Wrong Answer"
        else:
            return result
    test_case = Testcase_Output.objects.filter(submit=submit).order_by('execution_time').reverse()
    return submit_result


def give_score(submit, request):
    if not submit.result:
        return
    if submit.result == 'Compiler Error':
        return
    if submit.submit_time < submit.contest.start_time:
        return
    if submit.submit_time >= submit.contest.end_time:
        return
    pro = submit.problem
    this_problem_prevous_submit = Submit.objects.filter(contest=submit.contest, problem=pro, result='Correct', submit_time__lte=submit.submit_time, user=submit.user, team=submit.team).exclude(pk=submit.pk)
    if this_problem_prevous_submit:
        return
    if 'active_team' in request.session:
        try:
            team = Team.objects.get(username=request.session.get('active_team'))
            total_users = team.member.all()

            if submit.result == 'Correct':
                for user in total_users:
                    user.score += int(50 * submit.problem.point)
                    user.save()
                team.score += int(50 * submit.problem.point)
                team.save()
                submit.score = int(50 * submit.problem.point)
                submit.save()
                
            else:
                for user in total_users:
                    user.score -= 5
                    user.save()
                team.score -= 5
                team.save()
                submit.score = -5
                submit.save()
                
        except Team.DoesNotExist:
            pass
    else:
        user = User.objects.get(pk=request.user.pk)
        
        if submit.result == 'Correct':
            user.score += int(50 * submit.problem.point)
            user.save()
            submit.score = int(50 * submit.problem.point)
            submit.save()
        else:
            user.score -= 5
            user.save()
            submit.score = -5
            submit.save()


@login_required
@team_auth
def submit(request):
    refresh_active_contest(request) # refersh the contest session
    current_contest_id = request.session.get('contest_741_852_963')
    my_scoreboard = []
    problem_list =  None
    try:
        current_contest = Contest.objects.get(pk=current_contest_id, start_time__lte=timezone.now())
    except Contest.DoesNotExist:
        current_contest = None
    if current_contest_id and current_contest:
        try:
            problem_list =  current_contest.problem.all().order_by('short_name')
        except Contest.DoesNotExist:
            problem_list = []
        my_scoreboard = my_score(request, current_contest.pk)
        if request.method == "POST":
            form = SubmitAnswer(request.POST, request.FILES)
            form.fields['problem'].queryset = problem_list
            if form.is_valid():
                post = form.save(commit=False)
                post.submit_time = timezone.now()
                post.user = request.user
                if 'active_team' in request.session:
                    active_team = Team.objects.get(username=request.session.get('active_team'))
                    post.team = active_team
                else:
                    active_team = None
                post.contest_id = current_contest_id
                post.submit_file = None
                post.save()
                post.submit_file = request.FILES.get('submit_file')
                post.save()
                result = judge(file_name=post.submit_file.path, problem=post.problem, language=post.language, submit=post)
                post.result = result
                post.save()
                this_contest = post.contest
                this_contest.last_update = timezone.now()
                this_contest.save()
                if active_team:
                    team_score_and_rank(this_contest, post.problem, active_team, result, post) # update score and rank table for team
                else:
                    user_score_and_rank(this_contest, post.problem, request.user, result, post) # update score and rank table for user
                output_files = Testcase_Output.objects.filter(submit = post)
                for i in output_files:
                    if i.result == "Correct":
                        continue
                    else:
                        if i.output_file.size > 2 * i.test_case.output.size:
                            os.system('rm '+i.output_file.path) 
                            os.system('touch '+i.output_file.path) 
                if this_contest.has_value:
                    give_score(post, request)
                return redirect('submit')
        else:
            form = SubmitAnswer()
            form.fields['problem'].queryset = problem_list
    else:
        form = None 
    try:
        current_contest = Contest.objects.get(pk=current_contest_id)
        q = Q(problem=None)
        for pro in current_contest.problem.all():
            q = q | Q(problem=pro)
        if 'active_team' in request.session:
            active_team = Team.objects.get(username=request.session.get('active_team'))
            all_current_contest_submits = Submit.objects.filter(q, contest_id=current_contest_id, team=active_team).order_by('submit_time').reverse()
        else:
            all_current_contest_submits = Submit.objects.filter(q, contest_id=current_contest_id, user=request.user, team=None).order_by('submit_time').reverse()
        for i in all_current_contest_submits:
            if i.submit_time > current_contest.end_time:
                i.result = 'Too Late'
    except Contest.DoesNotExist:
        current_contest = None
        all_current_contest_submits = []
    return render(request, 'submit.html', {'form': form, 'all_current_contest_submits': all_current_contest_submits, 'my_scoreboard': my_scoreboard, 'problem_list': problem_list})    


def problem_list(request):
    refresh_active_contest(request) # refersh the contest session
    active_contest_id = request.session.get('contest_741_852_963')
    if not active_contest_id:
        return []
    try:
        problem = Contest.objects.get(pk=active_contest_id, start_time__lte=timezone.now()).problem.all()
    except Contest.DoesNotExist:
        problem = []
    problem = sorted(problem, key=lambda x: x.title.lower())
    return problem


@login_required
@team_auth
def active_contest_problem(request):
    problem = problem_list(request)
    return render(request, 'problem.html', {'problem': problem})


@login_required
@team_auth
def active_contest_problem_refresh(request):
    problem = problem_list(request)
    return render(request, 'problem_refresh.html', {'problem': problem})


@login_required
@team_auth
def ajax_submit_process(request):
    active_contest_id = request.session.get('contest_741_852_963')
    contest = Contest.objects.get(id=active_contest_id)
    file = request.GET.get('file')
    problem_id = request.GET.get('problem')
    lang_id = request.GET.get('language')
    file_extension = None
    file_name = file
    try:
        index = file_name[::-1].index('.')
        try:
            slash_index = file_name[::-1].index('/')
            if index < slash_index:
                file_extension = file_name[::-1][:index][::-1]
        except ValueError:
            file_extension = file_name[::-1][:index][::-1]
    except ValueError:
        pass
    total_lang = Language.objects.all()
    best_lang = None
    if file_extension:
        file_extension = file_extension.lower()
        for i in total_lang:
            if file_extension == i.extension.lower():
                best_lang = i.id
                break
    if not best_lang and lang_id:
        best_lang = int(lang_id)
    best_problem = None
    if not problem_id:
        total_pro = contest.problem.all()
        file_name = file
        try:
            index = file_name[::-1].index('\\')
            file_name = file_name[::-1][:index][::-1]
        except ValueError:
            pass
        for i in total_pro:
            if i.title.lower() in file_name.lower():
                best_problem = i.id
                break
    response_data = {'best_lang': best_lang, 'best_problem': best_problem}
    return JsonResponse(response_data , content_type="application/json")


def scoreboard_summary_public(contest, category=None):
    total_problems = contest.problem.all().order_by('short_name')
    q = Q(problem=None)
    for pro in contest.problem.all():
        q = q | Q(problem=pro)
    problem_summary_dict = {i:[0, 0] for i in total_problems}
    team_rank_cache = Rankcache_team_public.objects.filter(contest=contest)
    team_score_cache = Scorecache_team_public.objects.filter(q, rank_cache__contest=contest)
    # if category == None:
    #     user_rank_cache = Rankcache_user_public.objects.filter(contest=contest)
    #     user_score_cache = Scorecache_user_public.objects.filter(q, rank_cache__contest=contest)
    if category == "System" or category == "Organization":
        user_rank_cache = Rankcache_user_public.objects.filter(contest=contest, user__category__category="System")|\
            Rankcache_user_public.objects.filter(contest=contest, user__category__category="Organization")
        user_score_cache = Scorecache_user_public.objects.filter(q, rank_cache__contest=contest, rank_cache__user__category__category="System")|\
            Scorecache_user_public.objects.filter(q, rank_cache__contest=contest, rank_cache__user__category__category="Organization")
    else:
        user_rank_cache = Rankcache_user_public.objects.filter(contest=contest, user__category__category="Participant")|\
            Rankcache_user_public.objects.filter(contest=contest, user__category__category="Observer")|\
            Rankcache_user_public.objects.filter(contest=contest, user__category__category="Self Registered")
        user_score_cache = Scorecache_user_public.objects.filter(q, rank_cache__contest=contest, rank_cache__user__category__category="Participant")|\
            Scorecache_user_public.objects.filter(q, rank_cache__contest=contest, rank_cache__user__category__category="Observer")|\
            Scorecache_user_public.objects.filter(q, rank_cache__contest=contest, rank_cache__user__category__category="Self Registered")
    total_user = 0
    total_point = 0
    total_time = 0
    for rank in user_rank_cache:
        total_user += 1
        total_point += rank.point
        total_time += rank.punish_time
    for rank in team_rank_cache:
        total_user += 1
        total_point += rank.point
        total_time += rank.punish_time
    for score in user_score_cache:
        problem_summary_dict[score.problem][0] += score.submission
        if score.is_correct:  
            problem_summary_dict[score.problem][1] += 1
    for score in team_score_cache:
        problem_summary_dict[score.problem][0] += score.submission
        if score.is_correct:  
            problem_summary_dict[score.problem][1] += 1
    if total_point == int(total_point): total_point = int(total_point)
    summary = [total_user, 'summary', total_point, total_time]
    for pro in total_problems:
        this_problem = "%d/%d"%tuple(problem_summary_dict[pro])
        summary.append(this_problem)
    return summary


def scoreboard_summary_jury(contest):
    total_problems = contest.problem.all().order_by('short_name')
    problem_summary_dict = {i:[0, 0] for i in total_problems}
  
    user_rank_cache = Rankcache_user_jury.objects.filter(contest=contest)  
    team_rank_cache = Rankcache_team_jury.objects.filter(contest=contest)

    q = Q(problem=None)
    for pro in contest.problem.all():
        q = q | Q(problem=pro)
 
    user_score_cache = Scorecache_user_jury.objects.filter(q, rank_cache__contest=contest)
    team_score_cache = Scorecache_team_jury.objects.filter(q, rank_cache__contest=contest)
   
    total_user = 0
    total_point = 0
    total_time = 0
    for rank in user_rank_cache:
        total_user += 1
        total_point += rank.point
        total_time += rank.punish_time
    for rank in team_rank_cache:
        total_user += 1
        total_point += rank.point
        total_time += rank.punish_time
    for score in user_score_cache:
        problem_summary_dict[score.problem][0] += score.submission
        if score.is_correct:  
            problem_summary_dict[score.problem][1] += 1
    for score in team_score_cache:
        problem_summary_dict[score.problem][0] += score.submission
        if score.is_correct:  
            problem_summary_dict[score.problem][1] += 1
    if total_point == int(total_point): total_point = int(total_point)
    summary = [total_user, 'summary', total_point, total_time]
    for pro in total_problems:
        this_problem = "%d/%d"%tuple(problem_summary_dict[pro])
        summary.append(this_problem)
    return summary


def first_solver(score_cache, problem_list, contest_start_time, role):
    first_solver_list = []
    for problem in problem_list:
        this_problem_submit = score_cache.filter(is_correct=True, problem=problem).order_by('correct_submit_time')
        this_problem_first_solver = []
        if this_problem_submit:
            first_time = time_gap(this_problem_submit[0].correct_submit_time, contest_start_time)
            for score in this_problem_submit:
                time = time_gap(score.correct_submit_time, contest_start_time)
                if time > first_time:
                    break
                else:
                    if role == "team":
                        first_solver_list.append((score.rank_cache.team ,problem))
                    else:
                        first_solver_list.append((score.rank_cache.user ,problem))
    return first_solver_list
     
def last_submit(score_cache, contest_start_time):
    last = contest_start_time
    for submit in score_cache:
        if submit.is_correct and submit.correct_submit_time:
            if last < submit.correct_submit_time:
                last = submit.correct_submit_time
    last_minute = time_gap(last, contest_start_time)
    return last_minute


def create_rank(table):
    for users in table:
        users[0] = 1000000 - users[0]
    table.sort()
    for users in table:
        users[0] = 1000000 - users[0]
    if table:
        table[0].append(1)
    for i in range(1, len(table)):
        if table[i][:3] == table[i-1][:3]:
            table[i].append('')
        else:
            table[i].append(i+1)
    return table

def calculate_problem_score_team_jury(score_cache_jury, total_problems, contest_start_time, first_solver_list, team_id):
    score_vs_problem = dict()
    for score in score_cache_jury:
        pro = score.problem
        if score.is_correct:
            time = time_gap(score.correct_submit_time, contest_start_time)
            if (score.rank_cache.team, pro) in first_solver_list:
                score_vs_problem[pro] = (score.submission, time, "#26ac0c", team_id, pro.id)
            else:
                score_vs_problem[pro] = (score.submission, time, "#2ef507", team_id, pro.id)
        else:
            score_vs_problem[pro] = (score.submission, -1, "#cd5c5c", team_id, pro.id)
    problem_display = []
    for pro in total_problems:
        if pro in score_vs_problem:
            problem_display.append(score_vs_problem[pro])
        else:
            problem_display.append((0,-1, "#ffffff", None, None))
    return problem_display

def calculate_problem_score_user_jury(score_cache_jury, total_problems, contest_start_time, first_solver_list, user_id):
    score_vs_problem = dict()
    for score in score_cache_jury:
        pro = score.problem
        if score.is_correct:
            time = time_gap(score.correct_submit_time, contest_start_time)
            if (score.rank_cache.user, pro) in first_solver_list:
                score_vs_problem[pro] = (score.submission, time, "#26ac0c", user_id, pro.id)
            else:
                score_vs_problem[pro] = (score.submission, time, "#2ef507", user_id, pro.id)
        else:
            score_vs_problem[pro] = (score.submission, -1, "#cd5c5c", user_id, pro.id)
    problem_display = []
    for pro in total_problems:
        if pro in score_vs_problem:
            problem_display.append(score_vs_problem[pro])
        else:
            problem_display.append((0,-1, "#ffffff", None, None))
    return problem_display


def calculate_problem_score_team_public(score_cache_jury, total_problems, contest_start_time, first_solver_list):
    score_vs_problem = dict()
    for score in score_cache_jury:
        pro = score.problem
        if score.is_correct:
            time = time_gap(score.correct_submit_time, contest_start_time)
            if (score.rank_cache.team, pro) in first_solver_list:
                score_vs_problem[pro] = (score.submission, time, "#26ac0c")
            else:
                score_vs_problem[pro] = (score.submission, time, "#2ef507")
        elif score.pending:
            if score.punish:
                score_vs_problem[pro] = ("%d+%d"%(score.punish, score.pending), -1, "#00ffff")
            else:
                score_vs_problem[pro] = (score.pending, -1, "#00ffff")
        else:
            score_vs_problem[pro] = (score.submission, -1, "#cd5c5c")
    problem_display = []
    for pro in total_problems:
        if pro in score_vs_problem:
            problem_display.append(score_vs_problem[pro])
        else:
            problem_display.append((0,-1, "#ffffff"))
    return problem_display


def calculate_problem_score_user_public(score_cache_jury, total_problems, contest_start_time, first_solver_list):
    score_vs_problem = dict()
    for score in score_cache_jury:
        pro = score.problem
        if score.is_correct:
            time = time_gap(score.correct_submit_time, contest_start_time)
            if (score.rank_cache.user, pro) in first_solver_list:
                score_vs_problem[pro] = (score.submission, time, "#26ac0c")
            else:
                score_vs_problem[pro] = (score.submission, time, "#2ef507")
        elif score.pending:
            if score.punish:
                score_vs_problem[pro] = ("%d+%d"%(score.punish, score.pending), -1, "#00ffff")
            else:
                score_vs_problem[pro] = (score.pending, -1, "#00ffff")
        else:
            score_vs_problem[pro] = (score.submission, -1, "#cd5c5c")
    problem_display = []
    for pro in total_problems:
        if pro in score_vs_problem:
            problem_display.append(score_vs_problem[pro])
        else:
            problem_display.append((0,-1, "#ffffff"))
    return problem_display


@login_required
@admin_or_jury_auth
def user_calculate_scoreboard_by_jury(request, contest_id, category):
    current_contest = Contest.objects.get(pk=contest_id)
    contest_start_time = current_contest.start_time
    total_users = current_contest.user.filter(category__category = category)
    total_problems = current_contest.problem.all().order_by('short_name')
    rank_cache_jury = Rankcache_user_jury.objects.filter(contest=current_contest, user__category__category=category)
    score_cache_jury = Scorecache_user_jury.objects.filter(rank_cache__contest=current_contest, rank_cache__user__category__category=category)
    first_solver_list = first_solver(score_cache_jury, total_problems, contest_start_time, role = "user")
    display = []
    for users in total_users:
        user_score_cache_jury = score_cache_jury.filter(rank_cache__user=users)
        problem_display = calculate_problem_score_user_jury(user_score_cache_jury, total_problems, contest_start_time, first_solver_list, user_id=users.id)
        user_rank_cache = rank_cache_jury.filter(user=users)[0]
        user_point = float(user_rank_cache.point)
        if user_point == int(user_point): user_point = int(user_point)
        last_submit_time = last_submit(score_cache_jury, contest_start_time)
        flag = "assets/img/countries/" + users.campus.flag() + ".png"
        this_user_row = [user_point, user_rank_cache.punish_time, last_submit_time, users.first_name + " " + users.last_name, users.campus.name, flag, problem_display]
        display.append(this_user_row)
    rank = create_rank(display)
    return rank


@login_required
@admin_or_jury_auth
def team_calculate_scoreboard_by_jury(request, contest_id):
    current_contest = Contest.objects.get(pk=contest_id)
    contest_start_time = current_contest.start_time
    total_teams = current_contest.team.all()
    total_problems = current_contest.problem.all().order_by('short_name')
    rank_cache_jury = Rankcache_team_jury.objects.filter(contest=current_contest)
    score_cache_jury = Scorecache_team_jury.objects.filter(rank_cache__contest=current_contest)
    first_solver_list = first_solver(score_cache_jury, total_problems, contest_start_time, role="team")
    display = []
    for teams in total_teams:
        team_score_cache_jury = score_cache_jury.filter(rank_cache__team=teams)
        problem_display = calculate_problem_score_team_jury(team_score_cache_jury, total_problems, contest_start_time, first_solver_list, team_id=teams.id)
        team_rank_cache = rank_cache_jury.filter(team=teams)[0]
        team_point = float(team_rank_cache.point)
        if team_point == int(team_point): team_point = int(team_point)
        last_submit_time = last_submit(score_cache_jury, contest_start_time)
        flag = "assets/img/countries/" + teams.campus.flag() + ".png"
        this_team_row = [team_point, team_rank_cache.punish_time, last_submit_time, teams.username, teams.campus.name, flag, problem_display]
        display.append(this_team_row)
    rank = create_rank(display)
    return rank


def user_calculate_scoreboard_by_public(request, contest_id, category):
    current_contest = Contest.objects.get(pk=contest_id)
    contest_start_time = current_contest.start_time
    total_users = current_contest.user.filter(category__category = category)
    total_problems = current_contest.problem.all().order_by('short_name')
    q = Q(problem=None)
    for pro in current_contest.problem.all():
        q = q | Q(problem=pro)
 
    now = timezone.now()
    if current_contest.frozen_time and current_contest.unfrozen_time and current_contest.frozen_time <= now and now < current_contest.unfrozen_time:
        rank_cache_public = Rankcache_user_public.objects.filter(contest=current_contest, user__category__category=category)
        score_cache_public = Scorecache_user_public.objects.filter(q, rank_cache__contest=current_contest, rank_cache__user__category__category=category)
    else:
        rank_cache_public = Rankcache_user_jury.objects.filter(contest=current_contest, user__category__category=category)
        score_cache_public = Scorecache_user_jury.objects.filter(q, rank_cache__contest=current_contest, rank_cache__user__category__category=category)
  
    first_solver_list = first_solver(score_cache_public, total_problems, contest_start_time, role = "user")
    display = []
    for users in total_users:
        user_score_cache_public = score_cache_public.filter(rank_cache__user=users)
        problem_display = calculate_problem_score_user_public(user_score_cache_public, total_problems, contest_start_time, first_solver_list)
        user_rank_cache = rank_cache_public.filter(user=users)[0]
        user_point = float(user_rank_cache.point)
        if user_point == int(user_point): user_point = int(user_point)
        last_submit_time = last_submit(score_cache_public, contest_start_time)
        flag = "assets/img/countries/" + users.campus.flag() + ".png"
        this_user_row = [user_point, user_rank_cache.punish_time, last_submit_time, users.first_name + " " + users.last_name, users.campus.name, flag, problem_display]
        display.append(this_user_row)
    rank = create_rank(display)
    return rank


def team_calculate_scoreboard_by_public(request, contest_id):
    current_contest = Contest.objects.get(pk=contest_id)
    contest_start_time = current_contest.start_time
    total_teams = current_contest.team.all()
    total_problems = current_contest.problem.all().order_by('short_name')

    q = Q(problem=None)
    for pro in current_contest.problem.all():
        q = q | Q(problem=pro)
 
    now = timezone.now()
    if current_contest.frozen_time and current_contest.unfrozen_time and current_contest.frozen_time <= now and now < current_contest.unfrozen_time:
        rank_cache_public = Rankcache_team_public.objects.filter(contest=current_contest)
        score_cache_public = Scorecache_team_public.objects.filter(q, rank_cache__contest=current_contest)
    else:
        rank_cache_public = Rankcache_team_jury.objects.filter(contest=current_contest)
        score_cache_public = Scorecache_team_jury.objects.filter(q, rank_cache__contest=current_contest)
  
    first_solver_list = first_solver(score_cache_public, total_problems, contest_start_time, role="team")
    display = []
    for teams in total_teams:
        team_score_cache_public = score_cache_public.filter(rank_cache__team=teams)
        problem_display = calculate_problem_score_team_public(team_score_cache_public, total_problems, contest_start_time, first_solver_list)
        team_rank_cache = rank_cache_public.filter(team=teams)[0]
        team_point = float(team_rank_cache.point)
        if team_point == int(team_point): team_point = int(team_point)
        last_submit_time = last_submit(score_cache_public, contest_start_time)
        flag = "assets/img/countries/" + teams.campus.flag() + ".png"
        this_team_row = [team_point, team_rank_cache.punish_time, last_submit_time, teams.username, teams.campus.name, flag, problem_display]
        display.append(this_team_row)
    rank = create_rank(display)
    return rank

@login_required
@team_auth
def scoreboard(request):
    refresh_active_contest(request) # refersh the contest session
    now = timezone.now()
    contest_id = request.session.get('contest_741_852_963')
    frozen = None
    if contest_id:
        current_contest = Contest.objects.get(pk=contest_id)
        unfrozen_time = current_contest.unfrozen_time
        if not unfrozen_time: unfrozen_time = current_contest.end_time
        if current_contest.last_update < unfrozen_time and now >= unfrozen_time:
            current_contest.last_update = unfrozen_time
            current_contest.save()
        if current_contest.last_update < current_contest.start_time and now >= current_contest.start_time:
            current_contest.last_update = current_contest.start_time
            current_contest.save()
        if current_contest.frozen_time and now >= current_contest.frozen_time and now < unfrozen_time:
            frozen = (current_contest.frozen_time, unfrozen_time)
        else:
            frozen = None
        total_problems = current_contest.problem.all().order_by('short_name')
        last_update = str(current_contest.last_update)
        scoreboard_in_session = request.session.get('scoreboard_contest_id_'+ str(contest_id))
        if now < current_contest.start_time:
            scoreboard = None
        elif scoreboard_in_session and scoreboard_in_session['last_update'] == last_update:
            scoreboard = scoreboard_in_session['score']
        else:
            team_scoreboard = team_calculate_scoreboard_by_public(request, contest_id)
            participant_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Participant')
            observer_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Observer')
            self_registered_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Self Registered')
            
            if request.user.category.category == "System":
                system_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'System')
                organization_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Organization')
            elif request.user.category.category == "Organization":
                organization_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Organization')
                system_scoreboard = []
            else:
                system_scoreboard = organization_scoreboard = []
            scoreboard = {
                'team_scoreboard': team_scoreboard, 
                'participant_scoreboard': participant_scoreboard, 
                'observer_scoreboard': observer_scoreboard,
                'self_registered_scoreboard': self_registered_scoreboard,
                'system_scoreboard': system_scoreboard,
                'organization_scoreboard': organization_scoreboard,
                }
            summary = scoreboard_summary_public(current_contest, category=request.user.category.category)
            scoreboard['summary'] = summary
            request.session['scoreboard_contest_id_'+ str(contest_id)] = {'last_update': last_update, 'score': scoreboard, 'contest_id': contest_id}
    else:
        scoreboard = total_problems = contest_title = current_contest = None
    return render(request, 'scoreboard.html', {'scoreboard': scoreboard, 'total_problems': total_problems, 'contest': current_contest,'frozen': frozen})


def scoreboard_refresh(request):
    refresh_active_contest(request) # refersh the contest session
    now = timezone.now()
    contest_id = request.session.get('contest_741_852_963')
    frozen = None
    if contest_id:
        current_contest = Contest.objects.get(pk=contest_id)
        unfrozen_time = current_contest.unfrozen_time
        if not unfrozen_time: unfrozen_time = current_contest.end_time
        if current_contest.last_update < unfrozen_time and now >= unfrozen_time:
            current_contest.last_update = unfrozen_time
            current_contest.save()
        if current_contest.last_update < current_contest.start_time and now >= current_contest.start_time:
            current_contest.last_update = current_contest.start_time
            current_contest.save()
        if current_contest.frozen_time and now >= current_contest.frozen_time and now < unfrozen_time:
            frozen = (current_contest.frozen_time, unfrozen_time)
        else:
            frozen = None
        total_problems = current_contest.problem.all().order_by('short_name')
        last_update = str(current_contest.last_update)
        scoreboard_in_session = request.session.get('scoreboard_contest_id_'+ str(contest_id))
        if now < current_contest.start_time:
            scoreboard = None
        elif scoreboard_in_session and scoreboard_in_session['last_update'] == last_update:
            scoreboard = scoreboard_in_session['score']
        else:
            team_scoreboard = team_calculate_scoreboard_by_public(request, contest_id)
            participant_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Participant')
            observer_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Observer')
            self_registered_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Self Registered')
            
            if request.user.category.category == "System":
                system_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'System')
                organization_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Organization')
            elif request.user.category.category == "Organization":
                organization_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Organization')
                system_scoreboard = []
            else:
                system_scoreboard = organization_scoreboard = []
            scoreboard = {
                'team_scoreboard': team_scoreboard, 
                'participant_scoreboard': participant_scoreboard, 
                'observer_scoreboard': observer_scoreboard,
                'self_registered_scoreboard': self_registered_scoreboard,
                'system_scoreboard': system_scoreboard,
                'organization_scoreboard': organization_scoreboard,
                }
            summary = scoreboard_summary_public(current_contest, category=request.user.category.category)
            scoreboard['summary'] = summary
            request.session['scoreboard_contest_id_'+ str(contest_id)] = {'last_update': last_update, 'score': scoreboard, 'contest_id': contest_id}
    else:
        scoreboard = total_problems = contest_title = current_contest = None
    return render(request, 'scoreboard_refresh.html', {'scoreboard': scoreboard, 'total_problems': total_problems, 'contest': current_contest, 'frozen': frozen})


def public_scoreboard(request):
    refresh_active_contest_public(request)
    now = timezone.now()
    contest_id = contest_id = request.session.get('public_contest_741_852_963')
    frozen = None
    if contest_id:
        current_contest = Contest.objects.get(pk=contest_id)
        unfrozen_time = current_contest.unfrozen_time
        if not unfrozen_time: unfrozen_time = current_contest.end_time
        if current_contest.last_update < unfrozen_time and now >= unfrozen_time:
            current_contest.last_update = unfrozen_time
            current_contest.save()
        if current_contest.last_update < current_contest.start_time and now >= current_contest.start_time:
            current_contest.last_update = current_contest.start_time
            current_contest.save()
        if current_contest.frozen_time and now >= current_contest.frozen_time and now < unfrozen_time:
            frozen = (current_contest.frozen_time, unfrozen_time)
        else:
            frozen = None
        total_problems = current_contest.problem.all().order_by('short_name')
        last_update = str(current_contest.last_update)
        scoreboard_in_session = request.session.get('public_scoreboard_contest_id_'+ str(contest_id))
        if now < current_contest.start_time:
            scoreboard = None
        elif scoreboard_in_session and scoreboard_in_session['last_update'] == last_update:
            scoreboard = scoreboard_in_session['score']
        else:
            team_scoreboard = team_calculate_scoreboard_by_public(request, contest_id)
            organization_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Organization')
            participant_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Participant')
            observer_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Observer')
            self_registered_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Self Registered')
            system_scoreboard = []
            scoreboard = {
                'team_scoreboard': team_scoreboard, 
                'participant_scoreboard': participant_scoreboard, 
                'observer_scoreboard': observer_scoreboard,
                'self_registered_scoreboard': self_registered_scoreboard,
                'system_scoreboard': system_scoreboard,
                'organization_scoreboard': organization_scoreboard,
                }
            summary = scoreboard_summary_public(current_contest)
            scoreboard['summary'] = summary
            request.session['public_scoreboard_contest_id_'+ str(contest_id)] = {'last_update': last_update, 'score': scoreboard, 'contest_id': contest_id}
    else:
        scoreboard = total_problems = contest_title = current_contest = None
    return render(request, 'public_scoreboard.html', {'scoreboard': scoreboard, 'total_problems': total_problems, 'contest': current_contest,'frozen': frozen})


def public_scoreboard_refresh(request):
    refresh_active_contest_public(request) # refersh the contest session
    now = timezone.now()
    contest_id = request.session.get('public_contest_741_852_963')
    frozen = None
    if contest_id:
        current_contest = Contest.objects.get(pk=contest_id)
        unfrozen_time = current_contest.unfrozen_time
        if not unfrozen_time: unfrozen_time = current_contest.end_time
        if current_contest.last_update < unfrozen_time and now >= unfrozen_time:
            current_contest.last_update = unfrozen_time
            current_contest.save()
        if current_contest.last_update < current_contest.start_time and now >= current_contest.start_time:
            current_contest.last_update = current_contest.start_time
            current_contest.save()
        if current_contest.frozen_time and now >= current_contest.frozen_time and now < unfrozen_time:
            frozen = (current_contest.frozen_time, unfrozen_time)
        else:
            frozen = None
        total_problems = current_contest.problem.all().order_by('short_name')
        last_update = str(current_contest.last_update)
        scoreboard_in_session = request.session.get('public_scoreboard_contest_id_'+ str(contest_id))
        if now < current_contest.start_time:
            scoreboard = None
        elif scoreboard_in_session and scoreboard_in_session['last_update'] == last_update:
            scoreboard = scoreboard_in_session['score']
        else:
            team_scoreboard = team_calculate_scoreboard_by_public(request, contest_id)
            participant_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Participant')
            observer_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Observer')
            self_registered_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Self Registered')
            organization_scoreboard = user_calculate_scoreboard_by_public(request, contest_id, 'Organization')
            system_scoreboard = []
            scoreboard = {
                'team_scoreboard': team_scoreboard, 
                'participant_scoreboard': participant_scoreboard, 
                'observer_scoreboard': observer_scoreboard,
                'self_registered_scoreboard': self_registered_scoreboard,
                'system_scoreboard': system_scoreboard,
                'organization_scoreboard': organization_scoreboard,
                }
            summary = scoreboard_summary_public(current_contest)
            scoreboard['summary'] = summary
            request.session['public_scoreboard_contest_id_'+ str(contest_id)] = {'last_update': last_update, 'score': scoreboard, 'contest_id': contest_id}
    else:
        scoreboard = total_problems = contest_title = current_contest = None
    return render(request, 'public_scoreboard_refresh.html', {'scoreboard': scoreboard, 'total_problems': total_problems, 'contest': current_contest})


@login_required
@admin_or_jury_auth
def jury_scoreboard(request):
    refresh_active_contest_in_admin(request) # refersh the contest session
    now = timezone.now()
    contest_id = request.session.get('contest_741_852_963_admin')
    if contest_id:
        current_contest = Contest.objects.get(pk=contest_id)
        total_problems = current_contest.problem.all().order_by('short_name')
        last_update = str(current_contest.last_update)
        scoreboard_in_session = request.session.get('admin_scoreboard_contest_id_'+ str(contest_id))
        if now < current_contest.start_time:
            scoreboard = None
        elif scoreboard_in_session and scoreboard_in_session['last_update'] == last_update:
            scoreboard = scoreboard_in_session['score']
        else:
            team_scoreboard = team_calculate_scoreboard_by_jury(request, contest_id)
            participant_scoreboard = user_calculate_scoreboard_by_jury(request, contest_id, 'Participant')
            observer_scoreboard = user_calculate_scoreboard_by_jury(request, contest_id, 'Observer')
            self_registered_scoreboard = user_calculate_scoreboard_by_jury(request, contest_id, 'Self Registered')
            system_scoreboard = user_calculate_scoreboard_by_jury(request, contest_id, 'System')
            organization_scoreboard = user_calculate_scoreboard_by_jury(request, contest_id, 'Organization')
            scoreboard = {
                'team_scoreboard': team_scoreboard, 
                'participant_scoreboard': participant_scoreboard, 
                'observer_scoreboard': observer_scoreboard,
                'self_registered_scoreboard': self_registered_scoreboard,
                'system_scoreboard': system_scoreboard,
                'organization_scoreboard': organization_scoreboard,
                }
            summary = scoreboard_summary_jury(current_contest)
            scoreboard['summary'] = summary
            request.session['admin_scoreboard_contest_id_'+ str(contest_id)] = {'last_update': last_update, 'score': scoreboard, 'contest_id': contest_id}
    else:
        scoreboard = total_problems = contest_title = current_contest = None
    role = check_role(request)
    if role == 'Admin':
        base_page = "admin_base_site.html"
    else:
        base_page = "jury_base.html"
    return render(request, 'jury_scoreboard.html', {'scoreboard': scoreboard, 'total_problems': total_problems, 'contest': current_contest, 'base_page': base_page})


def jury_scoreboard_refresh(request):
    refresh_active_contest_in_admin(request) # refersh the contest session
    now = timezone.now()
    contest_id = request.session.get('contest_741_852_963_admin')
    if contest_id:
        current_contest = Contest.objects.get(pk=contest_id)
        total_problems = current_contest.problem.all().order_by('short_name')
        last_update = str(current_contest.last_update)
        scoreboard_in_session = request.session.get('admin_scoreboard_contest_id_'+ str(contest_id))
        if now < current_contest.start_time:
            scoreboard = None
        elif scoreboard_in_session and scoreboard_in_session['last_update'] == last_update:
            scoreboard = scoreboard_in_session['score']
        else:
            team_scoreboard = team_calculate_scoreboard_by_jury(request, contest_id)
            participant_scoreboard = user_calculate_scoreboard_by_jury(request, contest_id, 'Participant')
            observer_scoreboard = user_calculate_scoreboard_by_jury(request, contest_id, 'Observer')
            self_registered_scoreboard = user_calculate_scoreboard_by_jury(request, contest_id, 'Self Registered')
            system_scoreboard = user_calculate_scoreboard_by_jury(request, contest_id, 'System')
            organization_scoreboard = user_calculate_scoreboard_by_jury(request, contest_id, 'Organization')
            scoreboard = {
                'team_scoreboard': team_scoreboard, 
                'participant_scoreboard': participant_scoreboard, 
                'observer_scoreboard': observer_scoreboard,
                'self_registered_scoreboard': self_registered_scoreboard,
                'system_scoreboard': system_scoreboard,
                'organization_scoreboard': organization_scoreboard,
                }
            summary = scoreboard_summary_jury(current_contest)
            scoreboard['summary'] = summary
            request.session['admin_scoreboard_contest_id_'+ str(contest_id)] = {'last_update': last_update, 'score': scoreboard, 'contest_id': contest_id}
    else:
        scoreboard = total_problems = contest_title = current_contest = None
    return render(request, 'jury_scoreboard_refresh.html', {'scoreboard': scoreboard, 'total_problems': total_problems, 'contest': current_contest})


@login_required
@admin_or_jury_auth
def view_submissions(request):
    now = timezone.now()
    refresh_active_contest_in_admin(request) # refersh the contest session
    all_contests = Contest.objects.filter(active_time__lte=now, deactivate_time__gte=now, enable=True)
    all_submissions = Submit.objects.filter(contest__active_time__lte=now, contest__deactivate_time__gte=now, contest__enable=True).order_by('submit_time').reverse()
    all_problems = set()
    for i in all_submissions:
        pro = (i.problem.id, i.problem.title)
        all_problems.add(pro)
    role = check_role(request)
    if role == 'Admin':
        base_page = "admin_base_site.html"
    else:
        base_page = "jury_base.html"
    return render(request, 'submissions.html', {'submit': all_submissions, 'all_problems':all_problems, 'all_contests': all_contests, 'base_page': base_page})


@login_required
@admin_or_jury_auth
def submission_filter(request):
    refresh_active_contest_in_admin(request) # refersh the contest session
    contest_id = int(request.GET.get('contest_id'))
    problem_id = int(request.GET.get('problem_id'))
    type_filter = request.GET.get('type')
    if problem_id == 0:
        if contest_id == 0:
            all_submissions = Submit.objects.all().order_by('submit_time').reverse()
        else:
            all_submissions = Submit.objects.filter(contest_id=contest_id).order_by('submit_time').reverse()
    else:
        if contest_id == 0:
            all_submissions = Submit.objects.filter(problem_id=problem_id).order_by('submit_time').reverse()
        else:
            all_submissions = Submit.objects.filter(contest_id=contest_id, problem_id=problem_id).order_by('submit_time').reverse()
    if type_filter == 'rejudge':
        return render(request, 'rejudge_filter.html', {'submit': all_submissions})
    elif type_filter == 'rescore':
        return render(request, 'rescore_filter.html', {'submit': all_submissions})
   
    return render(request, 'submission_filter.html', {'submit': all_submissions})


def read_from_file(files):
    files.open(mode='r')
    try:
        file_list = files.readlines()
    except UnicodeDecodeError:
        file_list = []
    submit_file = ''
    for i in file_list:
        submit_file +=  i
    files.close()
    return submit_file


@login_required
@admin_or_jury_auth_and_submit_exist
def submission_detail(request, submit_id):
    refresh_active_contest_in_admin(request) # refersh the contest session
    submit = Submit.objects.get(pk=submit_id)
    answer_file = submit.submit_file
    submit_file = read_from_file(answer_file)    
    file_name = answer_file.name
    try:
        index = file_name[::-1].index('/')
        file_name = file_name[::-1][:index][::-1]
    except Exception:
        pass
    # detail about the test cases
    all_user_testcases = Testcase_Output.objects.filter(submit=submit).order_by('test_case')
    run_testcases = [ i.test_case for i in all_user_testcases]
    testcase_correct_answer = TestCase.objects.filter(problem=submit.problem).order_by('name')
    all_user_answers = {}
    all_correct_answers = {}
    for i in all_user_testcases:
        user_answer_file = i.output_file
        all_user_answers[i.test_case.id] = read_from_file(user_answer_file).strip().split('\n')
    for j in testcase_correct_answer:
        correct_answer_file = j.output
        all_correct_answers[j.id] = read_from_file(correct_answer_file).strip().split('\n')
    submit_detail = []
    for i in all_user_testcases:
        execution_time = float(i.execution_time)
        if not execution_time == 0:execution_time = ('%f' % execution_time)
        testcase_id = i.test_case.id
        result = i.result

        url = i.test_case.input.url
        file_path = url
        try:
            index = file_path[::-1].index('/')
            file_path = file_path[::-1][:index][::-1]
        except Exception:
            pass
        testcase_input_file = (url, file_path)

        url = i.test_case.output.url
        file_path = url
        try:
            index = file_path[::-1].index('/')
            file_path = file_path[::-1][:index][::-1]
        except Exception:
            pass
        testcase_output_file = (url, file_path)

        url = Testcase_Output.objects.get(test_case=i.test_case, submit=submit).output_file.url
        file_path = url
        try:
            index = file_path[::-1].index('/')
            file_path = file_path[::-1][:index][::-1]
        except Exception:
            pass
        user_output_file = (url, file_path)

        answer_compare = []
        x = all_correct_answers[testcase_id]
        y = all_user_answers[testcase_id]
        for k in range(min(len(x), len(y))):
            answer_compare.append((x[k], y[k]))
        submit_detail.append((testcase_id, result, answer_compare, testcase_input_file, testcase_output_file, user_output_file, execution_time))
    for i in testcase_correct_answer:
        if i in run_testcases:
            continue
        else:
            submit_detail.append((i.id, "Not Run", [], (None, None), (None, None), (None, None), 0))
    role = check_role(request)
    if role == 'Admin':
        base_page = "admin_base_site.html"
    else:
        base_page = "jury_base.html"
    return render(request, 'submission_detail.html', {'submit': submit, 'submit_file': submit_file, 'file_name': file_name, 'submit_detail': submit_detail, 'base_page': base_page})


@login_required
@admin_or_jury_auth
def specific_problem_submission(request):
    user_or_team = request.GET.get('type')
    problem_id = request.GET.get('problem_id')
    user_id = request.GET.get('user_id')
    refresh_active_contest_in_admin(request) # refersh the contest session
    contest_id = request.session.get('contest_741_852_963_admin')    
    current_contest = Contest.objects.get(pk=contest_id)
    if user_or_team == 'Team':
        this_problem_and_user_submissions = Submit.objects.filter(contest_id=contest_id, problem_id=problem_id, team_id=user_id, submit_time__gte=current_contest.start_time, submit_time__lte=current_contest.end_time).order_by('submit_time')
    else:
        this_problem_and_user_submissions = Submit.objects.filter(contest_id=contest_id, problem_id=problem_id, user_id=user_id, team=None, submit_time__gte=current_contest.start_time, submit_time__lte=current_contest.end_time).order_by('submit_time')
    correct = False
    specific_submissions = list()
    for i in this_problem_and_user_submissions:
        if correct:
            break
        elif i.result == 'Correct':
            correct = True
            specific_submissions.append(i)
        else:
            specific_submissions.append(i)
    role = check_role(request)
    if role == 'Admin':
        base_page = "admin_base_site.html"
    else:
        base_page = "jury_base.html"
    return render(request, 'specific_problem_submission.html', {'submit': specific_submissions, 'category': user_or_team, 'base_page': base_page})


@login_required
@admin_auth_and_submit_exist
def single_rejudge(request, submit_id):
    refresh_active_contest_in_admin(request) # refersh the contest session
    single_submit = Submit.objects.get(pk=submit_id)
    submit = [single_submit]
    return render(request, 'single_user_rejudge.html', {'submit': submit})


@login_required
@admin_auth
def multi_rejudge(request, problem_id, user_id, user_or_team):
    refresh_active_contest_in_admin(request) # refersh the contest session
    contest_id = request.session.get('contest_741_852_963_admin')    
    current_contest = Contest.objects.get(pk=contest_id)
    if user_or_team == 'team':
        submit = Submit.objects.filter(contest_id=contest_id, problem_id=problem_id, team_id=user_id, submit_time__gte=current_contest.start_time, submit_time__lte=current_contest.end_time).order_by('submit_time')
    else:
        submit = Submit.objects.filter(contest_id=contest_id, problem_id=problem_id, user_id=user_id, team=None, submit_time__gte=current_contest.start_time, submit_time__lte=current_contest.end_time).order_by('submit_time')
    correct = False
    specific_submissions = list()
    for i in submit:
        if correct:
            break
        elif i.result == 'Correct':
            correct = True
            specific_submissions.append(i)
        else:
            specific_submissions.append(i)
    return render(request, 'single_user_rejudge.html', {'submit': specific_submissions})


def rejudge_give_score(submit, prevous_submit_result):
    if submit.submit_time < submit.contest.start_time:
        return
    if submit.submit_time >= submit.contest.end_time:
        return
    pro = submit.problem
    this_problem_prevous_submit = Submit.objects.filter(contest=submit.contest, problem=pro, result='Correct', submit_time__lte=submit.submit_time, user=submit.user, team=submit.team).exclude(pk=submit.pk)
    if this_problem_prevous_submit:
        return
    if submit.result == 'Compiler Error':
        submit.score = 0
        submit.save()
        if prevous_submit_result == 'Compiler Error':
            return
        elif prevous_submit_result == 'Correct':
            if submit.team:
                for user in submit.team.member.all():
                    user.score -= int(50 * submit.problem.point)
                    user.save()
                team = submit.team
                team.score -= int(50 * submit.problem.point)
                team.save()
            else:
                user = submit.user
                user.score -= int(50 * submit.problem.point)
                user.save()
        else:
            if submit.team:
                for user in submit.team.member.all():
                    user.score += 5
                    user.save()
                team = submit.team
                team.score += 5
                team.save()
            else:
                user = submit.user
                user.score += 5
                user.save()
    elif submit.result == "Correct":
        this_problem_later_submit = Submit.objects.filter(contest=submit.contest, problem=pro, submit_time__gte=submit.submit_time, user=submit.user, team=submit.team).exclude(pk=submit.pk).exclude(score=0)
        for later_submit in this_problem_later_submit:
            if later_submit.team:
                for user in later_submit.team.member.all():
                    _user = user
                    _user.score -= later_submit.score
                    _user.save()
                team = later_submit.team
                team.score -= later_submit.score
                team.save()
            else:

                user = later_submit.user
                user.score -= later_submit.score
                user.save()
            later_submit.score = 0
            later_submit.save()
        submit.score = int(50 * submit.problem.point)
        submit.save()
        if prevous_submit_result == 'Correct':
            return
        elif prevous_submit_result == 'Compiler Error':
            if submit.team:
                for user in submit.team.member.all():
                    _user = user
                    _user.score += int(50 * submit.problem.point)
                    _user.save()
                _team = submit.team
                _team.score += int(50 * submit.problem.point)
                _team.save()
            else:
                _user = submit.user
                _user.score += int(50 * submit.problem.point)
                _user.save()
        else:
            if submit.team:
                for user in submit.team.member.all():
                    _user = user
                    _user.score += int(50 * submit.problem.point)+5
                    _user.save()
                _team = Team.objects.get(pk=submit.team.pk)
                _team.score += int(50 * submit.problem.point)+5
                _team.save()
            else:
                _user = submit.user
                _user.score += int(50 * submit.problem.point)+5 
                _user.save()
    else:
        if prevous_submit_result == 'Compiler Error':
            if submit.team:
                for user in submit.team.member.all():
                    _user = user
                    _user.score += 5
                    _user.save()
                _team = submit.team
                _team.score += 5
                _team.save()
            else:
                _user = submit.user
                _user.score += 5
                _user.save()
        elif prevous_submit_result == 'Correct':
            if submit.team:
                for user in submit.team.member.all():
                    _user = user
                    _user.score -= int(50 * submit.problem.point)+5
                    _user.save()
                _team = submit.team
                _team.score -= int(50 * submit.problem.point)+5
                _team.save()
            else:
                _user = submit.user
                _user.score -= int(50 * submit.problem.point)+5
                _user.save()


def update_score_and_rank(submit, prevous_submit_result, result):
    point = submit.problem.point
    contest = submit.contest
    if submit.team:
        rank_cache_jury = Rankcache_team_jury.objects.get(team=submit.team, contest=contest)
        rank_cache_public = Rankcache_team_public.objects.get(team=submit.team, contest=contest)
        try:
            score_cache_jury = Scorecache_team_jury.objects.get(rank_cache=rank_cache_jury, problem=submit.problem)
        except Scorecache_team_jury.DoesNotExist:
            score_cache_jury = Scorecache_team_jury(rank_cache=rank_cache_jury, problem=submit.problem)
            score_cache_jury.save()            
        try:
            score_cache_public = Scorecache_team_public.objects.get(rank_cache=rank_cache_public, problem=submit.problem)
        except Scorecache_team_public.DoesNotExist:
            score_cache_public = Scorecache_team_public(rank_cache=rank_cache_public, problem=submit.problem)
            score_cache_public.save()
    else:
        rank_cache_jury = Rankcache_user_jury.objects.get(user=submit.user, contest=contest)
        rank_cache_public = Rankcache_user_public.objects.get(user=submit.user, contest=contest)
        try:
            score_cache_jury = Scorecache_user_jury.objects.get(rank_cache=rank_cache_jury, problem=submit.problem)
        except Scorecache_user_jury.DoesNotExist:
            score_cache_jury = Scorecache_user_jury(rank_cache=rank_cache_jury, problem=submit.problem)
            score_cache_jury.save()
        try:
            score_cache_public = Scorecache_user_public.objects.get(rank_cache=rank_cache_public, problem=submit.problem)
        except Scorecache_user_public.DoesNotExist:
            score_cache_public = Scorecache_user_public(rank_cache=rank_cache_public, problem=submit.problem)
            score_cache_public.save()
    if score_cache_jury.is_correct:
        rank_cache_jury.point -= point 
        rank_cache_jury.punish_time -= (20 * score_cache_jury.punish + time_gap(score_cache_jury.correct_submit_time, contest.start_time))
        rank_cache_jury.save()
    score_cache_jury.is_correct = False
    score_cache_jury.punish = 0
    score_cache_jury.submission = 0
    score_cache_jury.correct_submit_time = None
    score_cache_jury.save()
    if score_cache_public.is_correct:
        rank_cache_public.point -= point
        rank_cache_public.punish_time -= (20 * score_cache_public.punish + time_gap(score_cache_public.correct_submit_time, contest.start_time))
        rank_cache_public.save() 
    score_cache_public.is_correct = False
    score_cache_public.punish = 0
    score_cache_public.submission = 0
    score_cache_public.correct_submit_time = None
    score_cache_public.pending = 0
    score_cache_public.save()
    if submit.team:
        all_submit = Submit.objects.filter(team =  submit.team, problem = submit.problem, contest=contest, submit_time__gte=contest.start_time,
                                            submit_time__lte=contest.end_time).exclude(team=None).exclude(result='').order_by('submit_time')
    else:
        all_submit = Submit.objects.filter(user = submit.user, problem=submit.problem, contest=contest, submit_time__gte=contest.start_time,
                                            submit_time__lte=contest.end_time, team=None).exclude(result='').order_by('submit_time')
    for sub in all_submit:
        score_cache_jury.submission += 1
        if sub.result == "Correct":
            score_cache_jury.correct_submit_time = sub.submit_time
            score_cache_jury.is_correct = True
            rank_cache_jury.point += point
            rank_cache_jury.punish_time += (20 * score_cache_jury.punish + time_gap(score_cache_jury.correct_submit_time, contest.start_time))
            rank_cache_jury.save()
            break
        elif not sub.result == "Compiler Error":
            score_cache_jury.punish += 1 
    score_cache_jury.save()   
    for sub in all_submit:
        score_cache_public.submission += 1
        if contest.frozen_time and contest.unfrozen_time and contest.frozen_time <= sub.submit_time and sub.submit_time < contest.unfrozen_time:
            score_cache_public.pending += 1
        elif sub.result == "Correct":
            score_cache_public.correct_submit_time = sub.submit_time
            score_cache_public.is_correct = True
            rank_cache_public.point += point
            rank_cache_public.punish_time += ( 20 * score_cache_public.punish + time_gap(score_cache_public.correct_submit_time, contest.start_time))
            rank_cache_public.save()
            break
        elif not sub.result == "Compiler Error":
            score_cache_public.punish += 1 
    score_cache_public.save()      


@login_required
@admin_auth
def ajax_rejudge(request):
    refresh_active_contest_in_admin(request) # refersh the contest session
    total_submits = request.GET.getlist('total_submit[]')  
    rejudge_submits = [int(i) for i in total_submits]
    result_dict = {}
    for submit_id in rejudge_submits:
        try:  
            submit = Submit.objects.get(pk=submit_id)
        except Submit.DoesNotExist:
            raise PermissionDenied
        prevous_submit_result = submit.result
        result = judge(file_name=submit.submit_file.path, problem=submit.problem, language=submit.language, submit=submit, rejudge=True)
        submit.result = result
        submit.save()
        update_score_and_rank(submit, prevous_submit_result, result)
        current_contest = submit.contest
        current_contest.last_update = timezone.now()
        current_contest.save()
        if current_contest.has_value:
            rejudge_give_score(submit, prevous_submit_result)        
        output_files = Testcase_Output.objects.filter(submit = submit)
        for i in output_files:
            if i.result == "Correct":
                continue
            else:
                if i.output_file.size > 2 * i.test_case.output.size:
                    os.system('rm '+i.output_file.path) 
                    os.system('touch '+i.output_file.path) 
        result_dict[submit_id] = submit.result
    response_data = {'result': result_dict}
    return JsonResponse(response_data , content_type="application/json")


@login_required
@admin_auth
def all_rejudge(request):
    now = timezone.now()
    refresh_active_contest_in_admin(request) # refersh the contest session
    all_contests = Contest.objects.filter(active_time__lte=now, deactivate_time__gte=now, enable=True)
    all_submissions = Submit.objects.filter(contest__active_time__lte=now, contest__deactivate_time__gte=now, contest__enable=True).order_by('submit_time').reverse()
    all_problems = set()
    for i in all_submissions:
        pro = (i.problem.id, i.problem.title)
        all_problems.add(pro)
    return render(request, 'rejudge.html', {'submit': all_submissions, 'all_contests': all_contests, 'all_problems': all_problems})


@login_required
@admin_auth
def ajax_rescore(request):
    refresh_active_contest_in_admin(request) # refersh the contest session
    total_submits = request.GET.getlist('total_submit[]')  
    rescore_submits = [int(i) for i in total_submits]
    result_dict = {}
    print(rescore_submits)
    for submit_id in rescore_submits:
        try:  
            submit = Submit.objects.get(pk=submit_id)
        except Submit.DoesNotExist:
            raise PermissionDenied
        prevous_submit_result = submit.result
        update_score_and_rank(submit, prevous_submit_result, prevous_submit_result)
        current_contest = submit.contest
        current_contest.last_update = timezone.now()
        current_contest.save()
        if current_contest.has_value:
            rejudge_give_score(submit, prevous_submit_result)        
    response_data = {}
    return JsonResponse(response_data, content_type="application/json")


@login_required
@admin_auth
def re_score(request):
    now = timezone.now()
    refresh_active_contest_in_admin(request) # refersh the contest session
    all_contests = Contest.objects.filter(active_time__lte=now, deactivate_time__gte=now, enable=True)
    all_submissions = Submit.objects.filter(contest__active_time__lte=now, contest__deactivate_time__gte=now, contest__enable=True).order_by('submit_time').reverse()
    all_problems = set()
    for i in all_submissions:
        pro = (i.problem.id, i.problem.title)
        all_problems.add(pro)
    return render(request, 're_score.html', {'submit': all_submissions, 'all_contests': all_contests, 'all_problems': all_problems})

