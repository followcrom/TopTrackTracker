# Generated by Django 4.2.7 on 2023-11-26 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TrendingTracks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('artist', models.CharField(max_length=200)),
                ('song', models.CharField(max_length=200)),
                ('album', models.CharField(max_length=200)),
                ('release_date', models.CharField(max_length=200)),
                ('popularity', models.CharField(max_length=200)),
                ('duration', models.CharField(max_length=200)),
                ('uri', models.CharField(max_length=200)),
            ],
        ),
    ]
