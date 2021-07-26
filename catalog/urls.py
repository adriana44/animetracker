from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('anime/', views.AnimeListView.as_view(), name='anime'),
    path('anime/<int:pk>', views.AnimeDetailView.as_view(), name='anime-detail'),
    path('studio/', views.StudioListView.as_view(), name='studios'),
    path('studio/<int:pk>', views.StudioDetailView.as_view(), name='studio-detail'),
    path('genre/', views.GenreListView.as_view(), name='genres'),
    path('genre/<int:pk>', views.GenreDetailView.as_view(), name='genre-detail'),
    path('watchlist/', views.WatchlistListView.as_view(), name='my-watchlist'),
    path('watchlist/add/<int:pk>', views.watchlist_add, name='watchlist-add'),
    path('watchlist/remove/<int:pk>', views.watchlist_remove, name='watchlist-remove'),
    # path('check-episodes/<int:pk>', views.check_new_episodes, name='check-episodes'),
    path('fetch-anime/', views.fetch_anime, name='fetch-anime'),
    path('set-all-last-aired-episodes/', views.set_all_last_aired_episodes, name='set-all-last-aired-episodes'),

    # path('testing/', views.fetch_anime, name='testing'),
    # path('testing/', views.populate_season, name='testing'),
]
