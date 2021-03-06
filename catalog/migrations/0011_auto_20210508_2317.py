# Generated by Django 3.1.7 on 2021-05-08 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0010_anime_mal_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='anime',
            name='airing_start',
        ),
        migrations.RemoveField(
            model_name='anime',
            name='currently_airing',
        ),
        migrations.AddField(
            model_name='anime',
            name='duration',
            field=models.TextField(default='duration', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='anime',
            name='rating',
            field=models.TextField(default=9, max_length=300),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='anime',
            name='scored_by',
            field=models.IntegerField(default=1000),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='anime',
            name='status',
            field=models.CharField(choices=[('air', 'Currently Airing'), ('fin', 'Finished Airing'), ('tba', 'to_be_aired')], default='air', max_length=3),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='anime',
            name='title_english',
            field=models.CharField(default='title english', max_length=1000),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='anime',
            name='genres',
            field=models.ManyToManyField(to='catalog.Genre'),
        ),
        migrations.AlterField(
            model_name='anime',
            name='members',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='anime',
            name='synopsis',
            field=models.TextField(max_length=5000),
        ),
    ]
