from django.db import models
from contest.models import Contest
from authentication.models import User, Team
# Create your models here.

class ClarificationFromUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__role': 'Team Member'})
    message = models.TextField()
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    send_time = models.DateTimeField()

    def __str__(self):
        return 'from ' + self.user.username + ' in ' + self.contest.title
       

class ClarificationFromTeam(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    message = models.TextField()
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    send_time = models.DateTimeField()

    def __str__(self):
        return 'from ' + self.team.username + ' in ' + self.contest.title
       
class ClarificationFromAdmin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__role': 'Team Member'}, blank=True, null=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True, null=True)
    message = models.TextField()
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=True)
    send_time = models.DateTimeField()

    def __str__(self):
        if self.user:
            return 'to ' + self.user.username + ' from admin in ' + self.contest.title
        elif self.team:
            return 'to ' + self.team.username + ' from admin in ' + self.contest.title
        else:
            return 'to all users and teams from admin in ' + self.contest.title

    