# Generated by Django 3.1.7 on 2021-05-04 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_auto_20210504_2317'),
    ]

    operations = [
        migrations.RenameField(
            model_name='anime',
            old_name='air_date',
            new_name='starting_air_date',
        ),
        migrations.RemoveField(
            model_name='anime',
            name='score',
        ),
        migrations.AddField(
            model_name='anime',
            name='air_day',
            field=models.CharField(choices=[('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'), ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'), ('Sun', 'Sunday')], default='Mon', max_length=3),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='anime',
            name='currently_airing',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='anime',
            name='mal_url',
            field=models.URLField(default='https://myanimelist.net/anime/season/schedule'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='anime',
            name='genre',
            field=models.ManyToManyField(help_text='Select a genre for this anime', to='catalog.Genre'),
        ),
    ]
