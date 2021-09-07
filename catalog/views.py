from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.http import HttpResponse
from django.views.decorators.http import require_POST

import json

from catalog.models import Genre, Season, Studio, Anime, UserProfile
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

    return render(request, 'index.html', context=context)


class AnimeListView(generic.ListView):
    model = Anime
    context_object_name = 'anime_list'
    template_name = 'catalog/anime_list.html'


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


@permission_required('catalog.season.change', raise_exception=True)
def populate_season(request):
    """Populates the Season table with Winter 2000 -> Fall 2021."""

    season_list = ['Winter', 'Spring', 'Summer', 'Fall']
    for year in range(2000, 2022):
        for season in season_list:
            new_season = Season(season=season, year=year)
            new_season.save()

    return index(request)


@login_required
def user_page(request):
    """View function for displaying a user's personal information."""
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
    """View function for profile editing form."""
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


@login_required
def edit_preferences(request):
    """View function for profile editing form."""
    if request.method == "POST":
        userprofile_form = UserProfileForm(request.POST, instance=request.user.userprofile)
        if userprofile_form.is_valid():
            userprofile_form.save()
            messages.success(request, 'Your preferences were successfully updated!')
        else:
            messages.error(request, 'Unable to complete request')
        return redirect(user_page)

    userprofile_form = UserProfileForm(instance=request.user.userprofile)
    context = {
        "userprofile": request.user.userprofile,
        "userprofile_form": userprofile_form,
    }

    return render(request, 'catalog/edit_preferences.html', context)


@login_required
@require_POST
def update_watchlist(request):
    """POST method for adding/removing anime to/from the user's watchlist."""
    watchlist = request.user.userprofile.watchlist
    anime_id = request.POST.get('anime_id', None)
    anime = get_object_or_404(Anime, pk=anime_id)

    # check whether the user already has this anime in their watchlist
    if watchlist.filter(id=anime_id).exists():
        # remove anime from watchlist
        watchlist.remove(anime)
        added = False
    else:
        # add anime to watchlist
        watchlist.add(anime)
        added = True

    return HttpResponse(json.dumps({'added': added}), content_type='application/json')


@login_required
def watchlist_remove(request, pk):
    """View for removing an anime from a user's watchlist."""
    watchlist = request.user.userprofile.watchlist
    anime = get_object_or_404(Anime, pk=pk)
    if watchlist.filter(id=pk).exists():
        watchlist.remove(anime)

    return render(request, 'catalog/user_profile.html')
