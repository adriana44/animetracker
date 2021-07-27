from django.contrib import admin

# Register your models here.
from .models import Genre, Season, Studio, Anime, UserProfile, StreamingWebsite


admin.site.register(Genre)
admin.site.register(Season)
admin.site.register(Studio)
admin.site.register(UserProfile)
admin.site.register(StreamingWebsite)

# @admin.register(Studio)
# class StudioAdmin(admin.ModelAdmin):
#     list_display = 'name'


@admin.register(Anime)
class AnimeAdmin(admin.ModelAdmin):
    list_display = ('title', 'members', 'season', 'status')
    list_filter = ('air_day', 'status', 'season')

