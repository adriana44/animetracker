# Generated by Django 3.1.7 on 2021-05-08 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0022_auto_20210509_0155'),
    ]

    operations = [
        migrations.AlterField(
            model_name='anime',
            name='synopsis',
            field=models.TextField(max_length=5000, null=True),
        ),
    ]