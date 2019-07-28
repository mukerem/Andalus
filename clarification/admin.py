from django.contrib import admin
from .models import ClarificationFromUser, ClarificationFromTeam, ClarificationFromAdmin
# Register your models here.

admin.site.register(ClarificationFromUser)
admin.site.register(ClarificationFromTeam)
admin.site.register(ClarificationFromAdmin)