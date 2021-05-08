from django.contrib import admin

# Register your models here.
from .models import Genre, Season, Studio, Anime


admin.site.register(Genre)
admin.site.register(Season)


admin.site.register(Studio)
# admin.site.register(Anime)

# @admin.register(Studio)
# class StudioAdmin(admin.ModelAdmin):
#     list_display = 'name'


@admin.register(Anime)
class AnimeAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_studios', 'display_genres')
    list_filter = ('season', 'air_day', 'genres')

