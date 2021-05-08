from django.db import models
from django.urls import reverse
# Create your models here.


class Genre(models.Model):
    """Model representing anime genre."""
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """String for representing the Model object."""
        return self.name


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
    mal_url = models.URLField()  # field url
    image_url = models.URLField()
    title = models.CharField(max_length=1000)
    title_english = models.CharField(max_length=1000, null=True)
    type = models.CharField(  # complete (pls check tho)
        max_length=3,
        choices=[
            ('TV', 'TV'),
            ('OVA', 'OVA'),
            ('Mov', 'Movie'),
            ('Sp', 'Special'),
            ('ONA', 'ONA'),
            ('Mus', 'Music'),
        ])
    source = models.TextField(max_length=50)
    episodes = models.IntegerField(null=True)
    status = models.CharField(
        max_length=3,
        choices=[
            ('air', 'Currently Airing'),
            ('fin', 'Finished Airing'),  # alias = complete, "Finished Airing"
            ('tba', 'to_be_aired'),  # alias = tba, upcoming
        ])
    duration = models.TextField(max_length=100)
    rating = models.TextField(max_length=300)  # e.g. PG-13
    score = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    scored_by = models.IntegerField(null=True)
    members = models.IntegerField()
    synopsis = models.TextField(max_length=5000, null=True)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True)  # premiered field
    air_day = models.CharField(  # de luat din broadcast field
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
    studios = models.ManyToManyField(Studio)  # studios field
    genres = models.ManyToManyField(Genre)

    class Meta:
        ordering = ['title']

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the url to access a detail record for this anime."""
        return reverse('anime-detail', args=[str(self.id)])

    # Delete this shit later
    def display_genres(self):
        """Create a string for the Genre. This is required to display genre in Admin."""
        return ', '.join(genre.name for genre in self.genres.all()[:3])

    display_genres.short_description = 'Genres'

    def display_studios(self):
        """Create a string for the Studio. This is required to display studios in Admin."""
        return ', '.join(studio.name for studio in self.studios.all()[:3])

    display_studios.short_description = 'Studios'
