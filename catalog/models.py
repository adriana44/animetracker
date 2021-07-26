from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Genre(models.Model):
    """Model representing anime genre."""
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a particular genre instance."""
        return reverse('genre-detail', args=[str(self.id)])


class Season(models.Model):
    """Model representing a season."""
    season = models.CharField(  # NEW
        max_length=6,
        choices=[
            ('Winter', 'Winter'),
            ('Spring', 'Spring'),
            ('Summer', 'Summer'),
            ('Fall', 'Fall'),
        ])
    year = models.IntegerField()

    class Meta:
        ordering = ['-year']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.season} {self.year}'


class Studio(models.Model):
    """Model representing a studio."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        """Returns the url to access a particular studio instance."""
        return reverse('studio-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.name


class Anime(models.Model):
    """Model representing an anime."""
    # id is the mal_id field
    mal_url = models.URLField()
    image_url = models.URLField()
    title = models.CharField(max_length=1000)
    type = models.TextField(max_length=50)
    source = models.TextField(max_length=50)
    episodes = models.IntegerField(null=True)
    last_aired_episode = models.IntegerField(null=True)
    status = models.CharField(
        max_length=3,
        choices=[
            ('air', 'Currently Airing'),
            ('fin', 'Finished Airing'),  # alias = complete, "Finished Airing"
            ('tba', 'to_be_aired'),  # alias = tba, upcoming
        ])
    score = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    members = models.IntegerField()
    synopsis = models.TextField(max_length=5000, null=True)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True)
    air_day = models.CharField(
        max_length=3,
        choices=[
            ('Mon', 'Monday'),
            ('Tue', 'Tuesday'),
            ('Wed', 'Wednesday'),
            ('Thu', 'Thursday'),
            ('Fri', 'Friday'),
            ('Sat', 'Saturday'),
            ('Sun', 'Sunday'),
        ]
    )
    studios = models.ManyToManyField(Studio)
    genres = models.ManyToManyField(Genre)

    class Meta:
        ordering = ['title']

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the url to access a detail record for this anime."""
        return reverse('anime-detail', args=[str(self.id)])

    def display_studios(self):
        """Create a string for the Studio. This is required to display studios in Admin."""
        return ', '.join(studio.name for studio in self.studios.all())

    display_studios.short_description = 'Studios'


class StreamingWebsite(models.Model):
    """Model representing a streaming website."""
    name = models.CharField(max_length=200, unique=True)
    url = models.URLField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String for representing the Model object."""
        return self.name


class UserProfile(models.Model):
    """Model representing a user profile."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    watchlist = models.ManyToManyField(Anime, blank=True)

    class Meta:
        ordering = ['user']

    def __str__(self):
        """String for representing the Model object."""
        return self.user.username
