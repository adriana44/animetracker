from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('anime/', views.AnimeListView.as_view(), name='anime'),
    path('anime/<int:pk>', views.AnimeDetailView.as_view(), name='anime-detail'),
    path('studio/', views.StudioListView.as_view(), name='studios'),
    path('studio/<int:pk>', views.StudioDetailView.as_view(), name='studio-detail'),
    path('testing/', views.fetch_anime, name='testing'),
]
