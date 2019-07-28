from django.db import models
from problem.models import Problem
from authentication.models import User, Team
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import date
from datetime import datetime

# Create your models here.

class Contest(models.Model):
    title = models.CharField(max_length=200)
    short_name = models.CharField(max_length=10)
    active_time = models.DateTimeField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    frozen_time = models.DateTimeField(blank=True, null=True)
    unfrozen_time = models.DateTimeField(blank=True, null=True)
    deactivate_time = models.DateTimeField()
    problem = models.ManyToManyField(Problem, blank=True)
    user = models.ManyToManyField(User, blank=True, limit_choices_to={'role__short_name': 'team'})
    team = models.ManyToManyField(Team, blank=True)
    photo = models.ImageField(blank=True, upload_to='', default='icpc.png')
    is_public =models.BooleanField(default=True)
    has_value =models.BooleanField(default=True)
    enable = models.BooleanField(default=True)
    last_update = models.DateTimeField(default=timezone.now)
    register_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('title', 'start_time', 'end_time')
    def __str__(self):
        return self.title

    def image_tag(self):
        return mark_safe('<img src="%s" width="150" height="150"/>' % self.photo.url)

    image_tag.short_description = 'Photo'
    image_tag.allow_tags = True
