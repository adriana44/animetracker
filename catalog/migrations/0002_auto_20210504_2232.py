# Generated by Django 3.1.7 on 2021-05-04 19:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('season', models.CharField(max_length=10)),
                ('year', models.IntegerField()),
            ],
        ),
        migrations.RenameModel(
            old_name='Producer',
            new_name='Studio',
        ),
        migrations.RenameField(
            model_name='anime',
            old_name='producer',
            new_name='studio',
        ),
        migrations.AlterField(
            model_name='anime',
            name='episodes',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='anime',
            name='season',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalog.season'),
        ),
    ]
