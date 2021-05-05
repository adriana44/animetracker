from django.db import models
from django.urls import reverse
# Create your models here.


class Genre(models.Model):
    """Model representing anime genre."""
    name = models.CharField(max_length=200, help_text='Enter an anime genre (e.g. Shounen)')

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String for representing the Model object."""
        return self.name


class Season(models.Model):
    """Model representing a season."""
    season = models.CharField(max_length=10)
    year = models.IntegerField()

    class Meta:
        ordering = ['year', 'season']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.season} {self.year}'


class Studio(models.Model):
    """Model representing a studio."""
    name = models.CharField(max_length=100)

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
    title = models.CharField(max_length=200)
    # Foreign Key used because anime can only have one studio, but studios can have multiple anime
    studio = models.ForeignKey(Studio, on_delete=models.SET_NULL, null=True)

    synopsis = models.TextField(max_length=2000, help_text='Enter a brief description of the anime')

    # ManyToManyField used because genre can contain many anime. Anime can cover many genres.
    genre = models.ManyToManyField(Genre, help_text='Select a genre for this anime')

    # Added by Adriana
    episodes = models.IntegerField()
    starting_air_date = models.DateField()
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True)
    currently_airing = models.BooleanField()
    mal_url = models.URLField()

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

    class Meta:
        ordering = ['title']

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the url to access a detail record for this anime."""
        return reverse('anime-detail', args=[str(self.id)])

    # Delete this shit later
    def display_genre(self):
        """Create a string for the Genre. This is required to display genre in Admin."""
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = 'Genre'
