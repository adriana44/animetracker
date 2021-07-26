from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views import generic

import json
import requests
import re

from bs4 import BeautifulSoup

from catalog.models import Genre, Season, Studio, Anime, UserProfile, StreamingWebsite


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
        # Add the item through the ManyToManyField (UserProfile => Anime)
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


def set_last_aired_episode(anime):
    streaming_website_url = 'https://gogoanime.pe/'
    # define the search query
    search_query = anime.title.lower().replace(' ', '%20')
    search_url = streaming_website_url + '/search.html?keyword=' + search_query

    if search_url is not None:
        print('Search url:', search_url)

        # set the headers like we are a browser,
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh;'
                          'Intel Mac OS X 10_10_1)'
                          'AppleWebKit/537.36 (KHTML, like Gecko)'
                          'Chrome/39.0.2171.95'
                          'Safari/537.36'
        }
        # download the search results page
        response = requests.get(search_url, headers=headers)
        # parse the downloaded page and grab all text
        soup = BeautifulSoup(response.text, "html.parser")
        # get the relative url to the anime page
        anime_link = soup.find('a', attrs={'href': re.compile("^/category")})
        # add it to the website's url to obtain the anime's url
        if anime_link is not None:
            anime_url = streaming_website_url + anime_link.get('href')
            print('Anime url:', anime_url)

            # define the base url for specific episodes
            base_episode_url = anime_url.replace('/category/', '') + '-episode-'
            print('Base episode url: ', base_episode_url)

            # starting from episode 1, check whether the page corresponding
            # to that specific episode exists
            # if it doesn't, update the last aired episode field
            ep_number = 1
            while True:
                episode_url = f'{base_episode_url}{ep_number}'
                print('Episode url: ', episode_url)
                response = requests.get(episode_url, headers=headers)
                soup = BeautifulSoup(response.text, "html.parser")
                if soup.h1.text == '404':
                    print('404 Page not found')
                    # set last aired episode to i-1
                    anime.last_aired_episode = ep_number - 1
                    anime.save()
                    break
                ep_number = ep_number + 1
        else:
            print('Anime url not found')
    else:
        print('Invalid streaming website')


def set_all_last_aired_episodes(request):
    anime_list = Anime.objects.all()
    for anime in anime_list.iterator():
        set_last_aired_episode(anime)

    # anime = Anime.objects.get(title='Fumetsu no Anata e')
    # set_last_aired_episode(anime)

    return index(request)


# def check_anime(streaming_website_url, anime):
#     """Checks whether a new episode of an anime appeared on the website."""
#
#     # define the search query
#     if streaming_website_url == 'https://gogoanime.pe/':
#         search_query = anime.title.lower().replace(' ', '%20')
#         search_url = streaming_website_url + '/search.html?keyword=' + search_query
#     else:
#         search_url = None
#
#     if search_url is not None:
#         print('Search url:', search_url)
#
#         # set the headers like we are a browser,
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Macintosh;'
#                           'Intel Mac OS X 10_10_1)'
#                           'AppleWebKit/537.36 (KHTML, like Gecko)'
#                           'Chrome/39.0.2171.95'
#                           'Safari/537.36'
#         }
#         # download the search results page
#         response = requests.get(search_url, headers=headers)
#         # parse the downloaded page and grab all text
#         soup = BeautifulSoup(response.text, "html.parser")
#         # get the relative url to the anime page
#         anime_link = soup.find('a', attrs={'href': re.compile("^/category")})
#         # add it to the website's url to obtain the anime's url
#         if anime_link is not None:
#             anime_url = streaming_website_url + anime_link.get('href')
#             print('Anime url:', anime_url)
#
#             episode_url = anime_url + '-episode-1'
#             response = requests.get(episode_url, headers=headers)
#             soup = BeautifulSoup(response.text, "html.parser")
#             if soup.title.text != 'Pages not found':
#                 i = 2
#                 while True:
#                     episode_url = anime_url + '-episode-' + i
#                     response = requests.get(episode_url, headers=headers)
#                     soup = BeautifulSoup(response.text, "html.parser")
#                     if soup.title.text == 'Pages not found':
#                         # set last aired episode to i-1
#                         anime.last_aired_episode = i - 1
#                         break
#                     i = i + 1
#         else:
#             print('Anime url not found')
#     else:
#         print('Invalid streaming website')
#
#
# def check_new_episodes(request):
#     # pk = streaming website id
#     # gogoanime = 1
#
#     streaming_queryset = StreamingWebsite.objects.filter(id=pk)
#
#     if streaming_queryset.exists():
#         # for anime in Anime.objects.all():
#         #     check_anime(streaming_queryset[0].url, anime)
#         check_anime(streaming_queryset[0].url, Anime.objects.get(title='Fumetsu no Anata e'))
#
#     return index(request)
