from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('anime/', views.AnimeListView.as_view(), name='anime'),
    path('anime/airing/', views.AiringAnimeListView.as_view(), name='airing-anime'),
    path('anime/<int:pk>', views.AnimeDetailView.as_view(), name='anime-detail'),
    path('studio/', views.StudioListView.as_view(), name='studios'),
    path('studio/<int:pk>', views.StudioDetailView.as_view(), name='studio-detail'),
    path('genre/', views.GenreListView.as_view(), name='genres'),
    path('genre/<int:pk>', views.GenreDetailView.as_view(), name='genre-detail'),
    path('watchlist/', views.WatchlistListView.as_view(), name='my-watchlist'),
    path('update-watchlist/', views.update_watchlist, name='update-watchlist'),
    path('watchlist-remove/<int:pk>', views.watchlist_remove, name='watchlist-remove'),
]

