from django.contrib.auth.models import User
from django.db.models.functions import datetime

import json
import requests
import re
import os

from bs4 import BeautifulSoup
from notifications.signals import notify

from catalog.models import Genre, Season, Studio, Anime, UserProfile


# once a week get the weekly schedule
def update_anime_table():
    """Updates the Anime table with the weekly schedule."""
    print(datetime.datetime.now().time())
    print('update anime table\n')

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
    # Dictionary for storing this week's schedule
    weekly_schedule = {
        "Mon": [],
        "Tue": [],
        "Wed": [],
        "Thu": [],
        "Fri": [],
        "Sat": [],
        "Sun": []
    }
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
                                  air_day=day[:3].capitalize())
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
                # If anime was already in the db, save last aired episode
                if Anime.objects.filter(id=new_anime.id).exists():
                    new_anime.last_aired_episode = Anime.objects.get(id=new_anime.id).last_aired_episode
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
                    # If so, assign it to the anime's 'studios' field
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

                # add anime to weekly schedule dictionary
                weekly_schedule[new_anime.air_day].append(new_anime.pk)

    current_dir = os.path.abspath(os.path.dirname(__file__))
    # save weekly schedule to file
    with open(os.path.join(current_dir, 'data/weekly_schedule.json'), 'w') as file:
        json.dump(weekly_schedule, file)


# once every 5 minutes, check if there are any new episodes
def check_todays_anime():
    """Checks and updates the last aired episode field for all anime scheduled to air today.
    In case a new episode is found, a notification is sent to all users who have
    the anime in their watchlist."""

    print(datetime.datetime.now().time())
    print('check todays anime\n')

    def check_for_new_episodes(anime):
        """Checks whether new episodes of the anime have been made available on gogoanime.
        In case a new episode is found, a notification is sent to all users who have
        the anime in their watchlist. This also updates the last_aired_episode and
        the latest_ep_url fields of the anime object."""

        def episode_exists(local_ep_number):
            """Checks whether the specified episode of the specified anime has aired.
            If it did, update the anime's last aired field. Returns a boolean."""
            episode_url = f'{base_episode_url}{local_ep_number}'
            # print('Episode url: ', episode_url)
            _response = requests.get(episode_url, headers=headers)
            _soup = BeautifulSoup(_response.text, "html.parser")
            if _soup.h1.text == '404':
                # check the url to the next episode
                # (fixes the issue of having a combined episode e.g. 4-5
                # with a single url to ep 4 and no url to ep 5)
                local_ep_number = local_ep_number + 1
                episode_url = f'{base_episode_url}{local_ep_number}'
                # print('Episode url: ', episode_url)
                _response = requests.get(episode_url, headers=headers)
                _soup = BeautifulSoup(_response.text, "html.parser")
                if _soup.h1.text == '404':
                    # print('404 Page not found')
                    # update the last_aired_episode and latest_ep_url fields
                    if local_ep_number > 2:
                        anime.last_aired_episode = local_ep_number - 2
                        anime.latest_ep_url = f'{base_episode_url}{anime.last_aired_episode}'
                        # update status if it's the last episode in the anime
                        if anime.episodes == anime.last_aired_episode:
                            anime.status = 'fin'
                        anime.save()
                    return False
            return True

        streaming_website_url = 'https://gogoanime.pe/'
        # define the search query (gogoanime-specific)
        search_query = re.sub(r'[^a-zA-Z0-9-]', '%20', anime.title.lower())
        search_query = search_query.replace('%20%20', '%20')
        # search_query = search_query.replace(' ', '%20')
        search_url = streaming_website_url + '/search.html?keyword=' + search_query

        if search_url is not None:
            # print('Search url:', search_url)

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
                # print('Anime url:', anime_url)

                # define the base url for specific episodes
                base_episode_url = anime_url.replace('/category/', '') + '-episode-'
                # print('Base episode url: ', base_episode_url)

                # starting from the last episode we know of, or otherwise episode 1,
                # check whether the page corresponding to that specific episode exists
                # if it doesn't, update the last aired episode field
                if anime.last_aired_episode is not None and anime.last_aired_episode != 0:
                    ep_number = anime.last_aired_episode
                    # print("last aired: ", anime.last_aired_episode)
                else:
                    ep_number = 1

                # save current last aired ep number
                prev_last_aired_episode = anime.last_aired_episode

                while episode_exists(ep_number):
                    ep_number = ep_number + 1

                # compare with new last aired ep value to see if it changed
                # if it did, notify all users who have the anime on their watchlist
                if anime.last_aired_episode != prev_last_aired_episode:
                    print(f'prev last aired ep = {prev_last_aired_episode}')
                    print(f'current last aired ep = {anime.last_aired_episode}')
                    user_profiles = UserProfile.objects.filter(watchlist__pk=anime.pk)
                    admin_user = User.objects.get(username='adriana')
                    for user_profile in user_profiles.iterator():
                        notify.send(sender=admin_user,
                                    recipient=user_profile.user,
                                    verb=f'Episode {anime.last_aired_episode} of {anime.title} is now available!',
                                    description=f'{anime.get_absolute_url()}')
            else:
                print(f'{anime.title} Anime url not found')
                print(f'search url: {search_url}\n')
        else:
            print('Invalid streaming website')

    current_dir = os.path.abspath(os.path.dirname(__file__))
    json_path = os.path.join(current_dir, 'data/weekly_schedule.json')

    with open(json_path) as json_file:
        weekly_schedule = json.load(json_file)
        today = datetime.datetime.now().strftime('%a')
        for anime_id in weekly_schedule[today]:
            check_for_new_episodes(Anime.objects.get(pk=anime_id))


def scheduled_job():
    pass
