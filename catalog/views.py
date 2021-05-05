from django.shortcuts import render
from catalog.models import Genre, Season, Studio, Anime
from django.views import generic


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
