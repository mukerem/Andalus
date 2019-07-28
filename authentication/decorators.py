from django.core.exceptions import PermissionDenied
from authentication.models import User, Role, Team
from problem.models import Problem, TestCase
from contest.models import Contest
from competitive.models import Submit

def admin_auth(function):
    def wrap(request, *args, **kwargs):
        admin = Role.objects.get(short_name='admin')
        if not request.user.is_admin and admin in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_problem_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Problem.objects.get(pk=kwargs['problem_id'])
        except Problem.DoesNotExist:
            raise PermissionDenied
        admin = Role.objects.get(short_name='admin')
        if not request.user.is_admin and  admin in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_testcase_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            TestCase.objects.get(pk=kwargs['testcase_id'])
        except TestCase.DoesNotExist:
            raise PermissionDenied
        admin = Role.objects.get(short_name='admin')
        if not request.user.is_admin and admin in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_contest_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Contest.objects.get(pk=kwargs['contest_id'])
        except Contest.DoesNotExist:
            raise PermissionDenied
        admin = Role.objects.get(short_name='admin')
        if not request.user.is_admin and admin in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_user_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            User.objects.get(pk=kwargs['user_id'])
        except User.DoesNotExist:
            raise PermissionDenied
        admin = Role.objects.get(short_name='admin')
        if not request.user.is_admin and admin in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_team_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Team.objects.get(pk=kwargs['team_id'])
        except Team.DoesNotExist:
            raise PermissionDenied
        admin = Role.objects.get(short_name='admin')
        if not request.user.is_admin and admin in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

def team_auth(function):
    def wrap(request, *args, **kwargs):
        team = Role.objects.get(short_name='team')
        if not request.user.is_admin and team in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

def check_team(function):
    def wrap(request, *args, **kwargs):
        team = Team.objects.filter(member=request.user)
        if team:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_auth_and_submit_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Submit.objects.get(pk=kwargs['submit_id'])
        except Submit.DoesNotExist:
            raise PermissionDenied
        admin = Role.objects.get(short_name='admin')
        if not request.user.is_admin and admin in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap



# jury user decorator

def jury_auth(function):
    def wrap(request, *args, **kwargs):
        jury = Role.objects.get(short_name='jury')
        if not request.user.is_admin and jury in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def jury_auth_and_problem_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Problem.objects.get(pk=kwargs['problem_id'])
        except Problem.DoesNotExist:
            raise PermissionDenied
        jury = Role.objects.get(short_name='jury')
        if not request.user.is_admin and jury in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def jury_auth_and_testcase_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            TestCase.objects.get(pk=kwargs['testcase_id'])
        except TestCase.DoesNotExist:
            raise PermissionDenied
        jury = Role.objects.get(short_name='jury')
        if not request.user.is_admin and jury in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def jury_auth_and_contest_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Contest.objects.get(pk=kwargs['contest_id'])
        except Contest.DoesNotExist:
            raise PermissionDenied
        jury = Role.objects.get(short_name='jury')
        if not request.user.is_admin and jury in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def jury_auth_and_user_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            User.objects.get(pk=kwargs['user_id'])
        except User.DoesNotExist:
            raise PermissionDenied
        jury = Role.objects.get(short_name='jury')
        if not request.user.is_admin and jury in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def jury_auth_and_team_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Team.objects.get(pk=kwargs['team_id'])
        except Team.DoesNotExist:
            raise PermissionDenied
        jury = Role.objects.get(short_name='jury')
        if not request.user.is_admin and jury in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap



def jury_auth_and_submit_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Submit.objects.get(pk=kwargs['submit_id'])
        except Submit.DoesNotExist:
            raise PermissionDenied
        jury = Role.objects.get(short_name='jury')
        if not request.user.is_admin and jury in request.user.role.all():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


# admin or jury

def admin_or_jury_auth(function):
    def wrap(request, *args, **kwargs):
        admin = Role.objects.get(short_name='admin')
        jury = Role.objects.get(short_name='jury')
        if not request.user.is_admin and (admin in request.user.role.all() or jury in request.user.role.all()):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def admin_or_jury_auth_and_submit_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Submit.objects.get(pk=kwargs['submit_id'])
        except Submit.DoesNotExist:
            raise PermissionDenied
        admin = Role.objects.get(short_name='admin')
        jury = Role.objects.get(short_name='jury')
        if not request.user.is_admin and (admin in request.user.role.all() or jury in request.user.role.all()):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

    
def admin_or_jury_or_team_auth_and_team_exist(function):
    def wrap(request, *args, **kwargs):
        try:
            Team.objects.get(pk=kwargs['team_id'])
        except Team.DoesNotExist:
            raise PermissionDenied
        admin = Role.objects.get(short_name='admin')
        jury = Role.objects.get(short_name='jury')
        team = Role.objects.get(short_name='team')
        if not request.user.is_admin and (admin in request.user.role.all() or jury in request.user.role.all() or team in request.user.role.all()):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
