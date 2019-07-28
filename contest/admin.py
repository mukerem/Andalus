from django.contrib import admin
from .models import Contest
# Register your models here.


class ContestAdmins(admin.ModelAdmin):
    fields = ('title', 'short_name', 'active_time', 'start_time', 'end_time', 'frozen_time', 'unfrozen_time', 'deactivate_time',
              'problem', 'user', 'team', 'image_tag', 'photo', 'is_public', 'has_value', 'enable', 'last_update', 'register_date')
    readonly_fields = ('image_tag',)
    filter_horizontal = ('problem', 'user', 'team',)



admin.site.register(Contest, ContestAdmins)