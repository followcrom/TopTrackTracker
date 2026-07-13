import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tttracker.settings')
django.setup()

# Import your model
from tttapp.models import TrendingTracks

from django.db.models import Max, Min

# Your script content
def analyze_trending_tracks():
    # Get the minimum ID
    min_id = TrendingTracks.objects.aggregate(Min('id'))['id__min']
    max_id = TrendingTracks.objects.aggregate(Max('id'))['id__max']
    total_records = TrendingTracks.objects.count()
    print(f"{total_records} total tracks\nMinID: {min_id} and MaxID: {max_id}\n\n ")

    all_records = TrendingTracks.objects.all()

    for record in all_records:
        print(
            f"ID: {record.id}, Artist: {record.artist}, Song: {record.song}, Album: {record.album}\n"
            f"Release Year: {record.release_year}, Popularity: {record.popularity}, Tempo: {record.tempo}\n"
            f"Energy: {record.energy}, Mood: {record.mood}\n"
        )

# Make sure to call the function
if __name__ == "__main__":
    analyze_trending_tracks()