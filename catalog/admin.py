from django.contrib import admin
from .models import *

admin.site.register(Genre)
admin.site.register(Season)
admin.site.register(Studio)
admin.site.register(StreamingWebsite)
admin.site.register(UserProfile)


@admin.register(Anime)
class AnimeAdmin(admin.ModelAdmin):
    list_display = ('title', 'season', 'status', 'air_day')
    list_filter = ('air_day', 'status', 'season')
