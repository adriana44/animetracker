# Generated by Django 3.1.7 on 2021-05-28 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0032_streamingwebsite'),
    ]

    operations = [
        migrations.AddField(
            model_name='anime',
            name='last_aired_episode',
            field=models.IntegerField(null=True),
        ),
    ]
