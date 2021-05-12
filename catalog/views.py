from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from catalog.models import Genre, Season, Studio, Anime, UserProfile
from django.views import generic
import json
import requests
from django.contrib.auth.mixins import  LoginRequiredMixin


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_anime = Anime.objects.count()
    num_seasonal_anime = Anime.objects.filter(season__season='Spring', season__year=2021).count()
    num_studios = Studio.objects.count()
    num_genres = Genre.objects.count()
    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_anime': num_anime,
        'num_seasonal_anime': num_seasonal_anime,
        'num_studios': num_studios,
        'num_genres': num_genres,
        'num_visits': num_visits,
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


class GenreListView(generic.ListView):
    model = Genre
    template_name = 'catalog/genre_list.html'


class GenreDetailView(generic.DetailView):
    model = Genre
    template_name = 'catalog/genre_detail.html'


class WatchlistListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing anime on the current user's watchlist."""
    model = UserProfile
    template_name = 'catalog/watchlist_list_anime_user.html'
    context_object_name = 'watchlist_list'
    # paginate_by = 10

    def get_queryset(self):
        """Return the watchlist of the current user."""
        return UserProfile.objects.get(user=self.request.user).watchlist.all()


@login_required
def watchlist_add(request, pk):
    anime_to_save = get_object_or_404(Anime, pk=pk)

    # Get the current user profile
    user = UserProfile.objects.get(user=request.user)

    # Get the current user's watchlist
    watchlist = UserProfile.objects.get(user=request.user).watchlist.all()

    # Check if the anime already exists in the user's watchlist
    if not watchlist.filter(id=pk).exists():
        # Add the item through the ManyToManyField (UserProfile => Watchlist)
        user.watchlist.add(anime_to_save)

    # Refresh the Anime List page
    return AnimeListView.as_view()(request)


@login_required
def watchlist_remove(request, pk):
    anime_to_rm = get_object_or_404(Anime, pk=pk)

    # Get the current user profile
    user = UserProfile.objects.get(user=request.user)

    # Get the current user's watchlist
    watchlist = UserProfile.objects.get(user=request.user).watchlist.all()

    # Check if the anime exists in the user's watchlist
    if watchlist.filter(id=pk).exists():
        # Remove the anime
        user.watchlist.remove(anime_to_rm)

    # Refresh the watchlist page
    return WatchlistListView.as_view()(request)


def get_season(air_date: str) -> Season:
    """Retrieves the season from a date."""
    year = air_date[:4]

    str_month = air_date[5:7]
    month = int(str_month)

    # Jan -> Mar
    if month < 4:
        season = 'Winter'
    # Apr -> Jun
    elif month < 7:
        season = 'Spring'
    # Jul -> Sep
    elif month < 10:
        season = 'Summer'
    # Oct -> Dec
    else:
        season = 'Fall'

    return Season(season=season, year=year)


def fetch_anime(request):
    """Updates the Anime database with the weekly schedule."""

    # Get the current week's anime schedule
    schedule_response = requests.get("https://api.jikan.moe/v3/schedule")

    # Load the json file
    week_json = json.loads(schedule_response.content.decode('utf-8'))

    days_of_the_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    # For each day of the week, create/update the respective anime entries
    for day in days_of_the_week:
        day_json = week_json[day]

        for anime in day_json:
            # Skip unpopular anime
            if anime['members'] > 10000:
                new_anime = Anime(mal_url=anime['url'],
                                  title=anime['title'],
                                  image_url=anime['image_url'],
                                  synopsis=anime['synopsis'],
                                  type=anime['type'],
                                  episodes=anime['episodes'],
                                  members=anime['members'],
                                  source=anime['source'],
                                  score=anime['score'],

                                  air_day=day[:3].capitalize(),
                                  status='air',
                                  )

                # Turn anime['airing_start'] into Season
                season = get_season(anime['airing_start'])
                # Check if the season is already in the db
                target_season = Season.objects.filter(season=season.season, year=season.year)
                # If it is, assign it
                if target_season.exists():
                    new_anime.season = Season.objects.get(season=season.season, year=season.year)
                # Otherwise, add it to the db and then assign it
                else:
                    new_season = Season(season=season.season, year=season.year)
                    new_season.save()
                    new_anime.season = new_season

                # Add anime's id
                new_anime.id = anime['mal_id']

                # Save anime to db
                # We have to save the Anime entry before adding the Genre and Studio fields
                # because it needs to have an id for the many-to-many relationships
                new_anime.save()

                # Get list of studio names
                studio_list = []
                for studio in anime['producers']:
                    studio_list.append(studio['name'])
                # For each studio name in the list
                for studio in studio_list:
                    # Check whether the studio is already in the db
                    target_studio = Studio.objects.filter(name=studio)
                    # If so, assign it
                    if target_studio.exists():
                        new_anime.studios.add(Studio.objects.get(name=studio))
                    # Otherwise, add it to the db then assign it
                    else:
                        new_studio = Studio(name=studio)
                        new_studio.save()
                        new_anime.studios.add(new_studio)

                # Get list of genre names
                genre_list = []
                for genre in anime['genres']:
                    genre_list.append(genre['name'])
                # For each genre name in the list, assign the respective Genre object
                for genre in genre_list:
                    target_genre = Genre.objects.get(name=genre)
                    new_anime.genres.add(target_genre)

    return index(request)


def populate_season(request):
    """Populates the Season table with Winter 2000 -> Fall 2021."""

    season_list = ['Winter', 'Spring', 'Summer', 'Fall']
    for year in range(2000, 2022):
        for season in season_list:
            new_season = Season(season=season, year=year)
            new_season.save()

    return index(request)
