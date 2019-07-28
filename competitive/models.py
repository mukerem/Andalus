from django.db import models
from problem.models import TestCase, Problem
from contest.models import Contest
from authentication.models import User, Team
from time import time
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
# Create your models here.

result_lists=(('Correct', 'Correct'), ('Time Limit Exceeded', 'Time Limit Exceeded'), ('Wrong Answer', 'Wrong Answer'), 
    ('Compiler Error', 'Compiler Error'), ('Memory Limit Exceeded', 'Memory Limit Exceeded'),
    ('Run Time Error', 'Run Time Error'), ('No Output', 'No Output')
)

def testcase_output_directory_upload(instance, filename):
    problem_title = instance.submit.problem.title.replace(' ', '')
    testcase_title = instance.test_case.name.replace(' ', '')
    # filename = filename.replace(' ','')
    if instance.submit.team:
        return 'file/team_{0}/{1}/{2}/output_{3}.txt'.format(instance.submit.team.id, problem_title, instance.submit.id, testcase_title)
    return 'file/user_{0}/{1}/{2}/output_{3}.txt'.format(instance.submit.user.id, problem_title, instance.submit.id, testcase_title)


def submit_file_directory_upload(instance, filename):
    problem_title = instance.problem.title.replace(' ', '')
    filename = filename.replace(' ','')
    if instance.team:
            return 'file/team_{0}/{1}/{2}/{3}'.format(instance.team.id, problem_title, instance.id, filename)
    return 'file/user_{0}/{1}/{2}/{3}'.format(instance.user.id, problem_title, instance.id, filename)
    # return 'file/user_{0}/{1}/{2}/{3}'.format(instance.user.id, problem_title, time() , filename)


class Language(models.Model):
    name = models.CharField(max_length=200, unique=True)
    compile_command = models.CharField(max_length=300, help_text="<\ffile_name.extension> and <<\ffile_name>> use @ to represent file_name with extension and # with out extension")
    run_command = models.CharField(max_length=300, help_text='<\ffile_name.extension> and <<\ffile_name>> use @ to represent file_name with extension and # with out extension')
    extension = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return self.name


class Submit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__role': 'Team Member'})
    team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True, null=True)
    submit_file = models.FileField(upload_to=submit_file_directory_upload)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    result = models.CharField(max_length=200, choices=result_lists)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    submit_time = models.DateTimeField()

    def __str__(self):
        return self.problem.title + ' by ' + self.user.username + ' for _sid '+str(self.pk)
   

class Testcase_Output(models.Model):
    output_file = models.FileField(upload_to=testcase_output_directory_upload)
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    submit = models.ForeignKey(Submit, on_delete=models.CASCADE)
    result = models.CharField(max_length=200, choices=result_lists)                                       
    execution_time = models.DecimalField(decimal_places=8, max_digits=12, default=0.00, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        unique_together = ('test_case', 'output_file')

    def __str__(self):
        return self.submit.__str__() + ' test case ' + self.test_case.name 
    
        
class Rankcache_user_jury(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, limit_choices_to={'enable': True})
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__role': 'Team Member'})
    point = models.DecimalField(default=0.0, decimal_places=2, max_digits=10, validators=[MinValueValidator(Decimal('0.00'))])
    punish_time = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('contest', 'user')

    def __str__(self):
        return self.user.username + " on " + self.contest.title
 
class Rankcache_team_jury(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, limit_choices_to={'enable': True})
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    point = models.DecimalField(default=0.0, decimal_places=2, max_digits=10, validators=[MinValueValidator(Decimal('0.00'))])
    punish_time = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('contest', 'team')

    def __str__(self):
        return self.team.username + " on " + self.contest.title


class Rankcache_user_public(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, limit_choices_to={'enable': True})
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__role': 'Team Member'})
    point = models.DecimalField(default=0.0, decimal_places=2, max_digits=10, validators=[MinValueValidator(Decimal('0.00'))])
    punish_time = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('contest', 'user')

    def __str__(self):
        return self.user.username + " on " + self.contest.title
 

class Rankcache_team_public(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, limit_choices_to={'enable': True})
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    point = models.DecimalField(default=0.0, decimal_places=2, max_digits=10, validators=[MinValueValidator(Decimal('0.00'))])
    punish_time = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('contest', 'team')

    def __str__(self):
        return self.team.username + " on " + self.contest.title
 

class Scorecache_user_jury(models.Model):
    rank_cache = models.ForeignKey(Rankcache_user_jury, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    submission = models.PositiveSmallIntegerField(default=0)
    punish = models.PositiveSmallIntegerField(default=0)
    pending = models.PositiveSmallIntegerField(default=0)
    correct_submit_time = models.DateTimeField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('rank_cache', 'problem')

    def __str__(self):
        return self.rank_cache.user.username + " on " + self.rank_cache.contest.title + ' for problem ' + self.problem.title


class Scorecache_team_jury(models.Model):
    rank_cache = models.ForeignKey(Rankcache_team_jury, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    submission = models.PositiveSmallIntegerField(default=0)
    punish = models.PositiveSmallIntegerField(default=0)
    pending = models.PositiveSmallIntegerField(default=0)
    correct_submit_time = models.DateTimeField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('rank_cache', 'problem')

    def __str__(self):
        return self.rank_cache.team.username + " on " + self.rank_cache.contest.title + ' for problem ' + self.problem.title

class Scorecache_user_public(models.Model):
    rank_cache = models.ForeignKey(Rankcache_user_public, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    submission = models.PositiveSmallIntegerField(default=0)
    punish = models.PositiveSmallIntegerField(default=0)
    pending = models.PositiveSmallIntegerField(default=0)
    correct_submit_time = models.DateTimeField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('rank_cache', 'problem')

    def __str__(self):
        return self.rank_cache.user.username + " on " + self.rank_cache.contest.title + ' for problem ' + self.problem.title


class Scorecache_team_public(models.Model):
    rank_cache = models.ForeignKey(Rankcache_team_public, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    submission = models.PositiveSmallIntegerField(default=0)
    punish = models.PositiveSmallIntegerField(default=0)
    pending = models.PositiveSmallIntegerField(default=0)
    correct_submit_time = models.DateTimeField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('rank_cache', 'problem')

    def __str__(self):
        return self.rank_cache.team.username + " on " + self.rank_cache.contest.title + ' for problem ' + self.problem.title


# class UserAttendance(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__role': 'Team Member'})
#     contest = models.ForeignKey(Contest, on_delete=models.CASCADE, limit_choices_to={'enable': True})

#     class Meta:
#         unique_together = ('contest', 'user')

#     def __str__(self):
#         return self.user.username + " on " + self.contest.title
 

# class TeamAttendance(models.Model):
#     team = models.ForeignKey(Team, on_delete=models.CASCADE)
#     contest = models.ForeignKey(Contest, on_delete=models.CASCADE, limit_choices_to={'enable': True})

#     class Meta:
#         unique_together = ('contest', 'team')

#     def __str__(self):
#         return self.team.username + " on " + self.contest.title

#         