# Generated by Django 4.2.7 on 2023-11-30 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tttapp', '0004_trendingtracks_artist_uri_trendingtracks_energy_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trendingtracks',
            name='artist_uri',
            field=models.CharField(max_length=200),
        ),
    ]
