# Generated by Django 3.1.7 on 2021-05-08 22:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0019_auto_20210509_0129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='anime',
            name='score',
            field=models.DecimalField(decimal_places=2, max_digits=4, null=True),
        ),
    ]
