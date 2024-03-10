# Generated by Django 4.2.7 on 2023-11-30 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tttapp', '0003_rename_release_date_trendingtracks_release_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='trendingtracks',
            name='artist_uri',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.AddField(
            model_name='trendingtracks',
            name='energy',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='trendingtracks',
            name='genres',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='trendingtracks',
            name='key',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='trendingtracks',
            name='tempo',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='trendingtracks',
            name='valence',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
