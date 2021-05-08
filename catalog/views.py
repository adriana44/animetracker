from django.shortcuts import render
from catalog.models import Genre, Season, Studio, Anime
from django.views import generic
import json
import requests


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_anime = Anime.objects.count()
    num_seasonal_anime = Anime.objects.filter(season__season='Spring', season__year=2021).count()
    num_studios = Studio.objects.count()
    num_genres = Genre.objects.count()

    context = {
        'num_anime': num_anime,
        'num_seasonal_anime': num_seasonal_anime,
        'num_studios': num_studios,
        'num_genres': num_genres,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class AnimeListView(generic.ListView):
    model = Anime
    context_object_name = 'anime_list'
    template_name = 'catalog/anime_list.html'
    # paginate_by = 2 # number of items to display on each page
    # Can access page 2 with the URL /catalog/anime/?page=2

    # def get_queryset(self):
    #     """Return the last 2 aired anime."""
    #     return Anime.objects.order_by('-starting_air_date')[:2]


class AnimeDetailView(generic.DetailView):
    model = Anime
    template_name = 'catalog/anime_detail.html'


class StudioListView(generic.ListView):
    model = Studio
    template_name = 'catalog/studio_list.html'


class StudioDetailView(generic.DetailView):
    model = Studio
    template_name = 'catalog/studio_detail.html'


def fetch_anime(request):
    schedule_response = requests.get("https://api.jikan.moe/v3/schedule")

    # days_of_the_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    days_of_the_week = ['sunday']
    for day in days_of_the_week:
        day_json = json.loads(schedule_response.content.decode('utf-8'))[day]

        # day_json = day_json[24:36]
        for anime_entry in day_json:
            mal_id = anime_entry['mal_id']
            anime_response = requests.get(f'http://api.jikan.moe/v3/anime/{mal_id}')
    
            anime = json.loads(anime_response.content.decode('utf-8'))
    
            mal_id = anime['mal_id']
            mal_url = anime['url']
            image_url = anime['image_url']
            title = anime['title']
            title_english = anime['title_english']
            type_ = anime['type']
            source = anime['source']
            episodes = anime['episodes']
    
            a_status = anime['status']
            if a_status == 'Currently Airing':
                status = 'air'
            elif a_status == 'Finished Airing' or a_status == 'Completed' or a_status == 'Complete':
                status = 'fin'
            else:
                status = 'tba'
    
            duration = anime['duration']
            rating = anime['rating']
            score = anime['score']
            scored_by = anime['scored_by']
            members = anime['members']
            synopsis = anime['synopsis']
    
            season = anime['premiered'].split()
            season_season = season[0]
            season_year = season[1]
    
            broadcast = anime['broadcast']
            air_day = broadcast[:3]
    
            studio_list = []
            for studio in anime['studios']:
                studio_list.append(studio['name'])
    
            genre_list = []
            for genre in anime['genres']:
                genre_list.append(genre['name'])

            # Create Anime object
            new_anime = Anime(mal_url=mal_url,
                              image_url=image_url,
                              title=title,
                              title_english=title_english,
                              type=type_,
                              source=source,
                              episodes=episodes,
                              status=status,  # issue
                              duration=duration,
                              rating=rating,
                              score=score,
                              scored_by=scored_by,
                              members=members,
                              synopsis=synopsis,
                              air_day=air_day,
                              )

            # Add anime's season
            target_season = Season.objects.filter(season=season_season, year=season_year)
            if target_season.exists():
                new_anime.season = Season.objects.get(season=season_season, year=season_year)
            else:
                new_season = Season(season=season_season, year=season_year)
                new_season.save()
                new_anime.season = new_season

            # Add anime's id
            new_anime.id = mal_id

            # Save anime to database
            new_anime.save()

            # Add anime's genres
            for genre in genre_list:
                target_genre = Genre.objects.get(name=genre)
                new_anime.genres.add(target_genre)

            # Add anime's studios
            for studio in studio_list:
                target_studio = Studio.objects.filter(name=studio)
                if target_studio.exists():
                    new_anime.studios.add(Studio.objects.get(name=studio))
                else:
                    new_studio = Studio(name=studio)
                    new_studio.save()
                    new_anime.studios.add(new_studio)

    return index(request)
