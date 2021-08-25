from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic

import json
import requests
import re

from bs4 import BeautifulSoup

from catalog.models import Genre, Season, Studio, Anime, UserProfile, StreamingWebsite
from catalog.forms import UserForm, UserProfileForm


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_anime = Anime.objects.count()
    num_seasonal_anime = Anime.objects.filter(status='air').count()
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

    def get_context_data(self, **kwargs):
        context = super(AnimeListView, self).get_context_data(**kwargs)
        context['watchlist'] = UserProfile.objects.get(user=self.request.user).watchlist.all()
        return context

    # paginate_by = 2 # number of items to display on each page
    # Can access page 2 with the URL /catalog/anime/?page=2

    # def get_queryset(self):
    #     """Return the last 2 aired anime."""
    #     return Anime.objects.order_by('-starting_air_date')[:2]


class AiringAnimeListView(generic.ListView):
    model = Anime
    context_object_name = 'anime_list'
    template_name = 'catalog/airing_anime_list.html'


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
    template_name = 'catalog/watchlist.html'
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

    # Load the watchlist page
    return WatchlistListView.as_view()(request)


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

    # Load the watchlist page
    return WatchlistListView.as_view()(request)


@permission_required('catalog.anime.change', raise_exception=True)
def update_anime_table(request):
    """Updates the Anime table with the weekly schedule."""

    def get_season(air_date: str) -> Season:
        """Retrieves the season from a date."""
        year = air_date[:4]

        str_month = air_date[5:7]
        month = int(str_month)

        # Jan -> Mar
        if month < 4:
            date_season = 'Winter'
        # Apr -> Jun
        elif month < 7:
            date_season = 'Spring'
        # Jul -> Sep
        elif month < 10:
            date_season = 'Summer'
        # Oct -> Dec
        else:
            date_season = 'Fall'

        return Season(season=date_season, year=year)

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
                                  status='air',
                                  air_day=day[:3].capitalize(),
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


@permission_required('catalog.season.change', raise_exception=True)
def populate_season(request):
    """Populates the Season table with Winter 2000 -> Fall 2021."""

    season_list = ['Winter', 'Spring', 'Summer', 'Fall']
    for year in range(2000, 2022):
        for season in season_list:
            new_season = Season(season=season, year=year)
            new_season.save()

    return index(request)


# REMOVE PRINTS
@permission_required('catalog.anime.change', raise_exception=True)
def set_all_last_aired_episodes(request):
    """Sets the last aired episode field for all anime in the database."""

    def set_last_aired_episode(anime):
        """Sets the last aired episode field of an anime by checking which episodes
        are available on gogoanime."""

        def episode_exists(local_ep_number):
            """Checks whether the specified episode of the specified anime has aired. Returns a boolean."""
            episode_url = f'{base_episode_url}{local_ep_number}'
            print('Episode url: ', episode_url)
            _response = requests.get(episode_url, headers=headers)
            _soup = BeautifulSoup(_response.text, "html.parser")
            if _soup.h1.text == '404':
                # check the url to the next episode
                # (fixes the issue of having a combined episode e.g. 4-5
                # with a single url to ep 4 and no url to ep 5)
                local_ep_number = local_ep_number + 1
                episode_url = f'{base_episode_url}{local_ep_number}'
                print('Episode url: ', episode_url)
                _response = requests.get(episode_url, headers=headers)
                _soup = BeautifulSoup(_response.text, "html.parser")
                if _soup.h1.text == '404':
                    print('404 Page not found')
                    # set the last aired episode field
                    if local_ep_number > 2:
                        anime.last_aired_episode = local_ep_number - 2
                        # update status if it's the last episode in the anime
                        if anime.episodes == anime.last_aired_episode:
                            anime.status = 'fin'
                        anime.save()
                    return False
            return True

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

                # starting from the last episode we know of, or otherwise episode 1,
                # check whether the page corresponding to that specific episode exists
                # if it doesn't, update the last aired episode field
                if anime.last_aired_episode is not None and anime.last_aired_episode != 0:
                    ep_number = anime.last_aired_episode
                else:
                    ep_number = 1

                while episode_exists(ep_number):
                    ep_number = ep_number + 1
            else:
                print('Anime url not found')
        else:
            print('Invalid streaming website')

    anime_list = Anime.objects.all()
    for _anime in anime_list.iterator():
        # if the anime is not finished
        if _anime.status != 'fin':
            set_last_aired_episode(_anime)

    return index(request)


@permission_required('catalog.anime.change', raise_exception=True)
def do_this_once(request):
    # anime_list = Anime.objects.all()
    # for anime in anime_list.iterator():
    #     if anime.episodes is not None and anime.episodes == anime.last_aired_episode:
    #         print(anime.title)
    #         anime.status = 'fin'
    #         anime.save()
    print('OK')
    return index(request)


@login_required
def user_page(request):
    user_form = UserForm(instance=request.user)
    user_profile_form = UserProfileForm(instance=request.user.userprofile)
    context = {
        "user": request.user,
        "user_form": user_form,
        "user_profile_form": user_profile_form
    }
    return render(request, 'catalog/user_profile.html', context)


@login_required
def edit_profile(request):
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Your profile was successfully updated!')
        else:
            messages.error(request, 'Unable to complete request')
        return redirect(user_page)

    user_form = UserForm(instance=request.user)
    context = {
        "user": request.user,
        "user_form": user_form,
    }

    return render(request, 'catalog/edit_profile.html', context)


def test(request):
    return render(request, 'base.html')
