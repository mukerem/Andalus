from django.contrib import admin
from .models import Language, Submit, Testcase_Output, Rankcache_user_public, Rankcache_team_public, Rankcache_user_jury, Rankcache_team_jury,\
		Scorecache_user_jury, Scorecache_team_jury,Scorecache_user_public, Scorecache_team_public
# Register your models here.

admin.site.register(Language)
admin.site.register(Submit)
admin.site.register(Testcase_Output)
admin.site.register(Rankcache_user_public)
admin.site.register(Rankcache_team_public)
admin.site.register(Rankcache_user_jury)
admin.site.register(Rankcache_team_jury)
admin.site.register(Scorecache_user_public)
admin.site.register(Scorecache_team_public)
admin.site.register(Scorecache_user_jury)
admin.site.register(Scorecache_team_jury)