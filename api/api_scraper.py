import csv
import os
import time
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Dict, List

from api.api_processors import Authenticator, SpotifyApiProcessor


# Dataclass to store main datasets.
@dataclass
class MainProcessor:
    tracks: List = []
    albums: List = []
    artists: List = []

    # def save_to_csv(file_name, csv_headers, csv_data):
    #     with open(file_name, "w", newline="") as csvfile:
    #         writer = csv.DictWriter(csvfile, fieldnames=csv_headers, extrasaction="ignore")
    #         writer.writeheader()
    #         writer.writerows(csv_data)

    # def save_data_to_csv(self, folder_path):
    #     for field in fields(self):
    #         file_name = os.path.join(folder_path, field.name)
    #         if field.type is List:
    #             csv_headers = [key for key in getattr(self, field.name)[0].keys()]
    #             csv_data = getattr(self, field.name)

    # Need to write data to SQL files for Inserts
    # need a function to write data to .csv


def main_processor(
    rolling_stones_scraped_data: list, folder_path: str
) -> MainProcessor:
    """
    1) Authenticate to Spotify API
    2) Loop trough Rolling Stones Top 500 dataset and Store Spotify API responses in MainProcessor Object.
    """

    # Authenticate
    authenticator = Authenticator("SPOTIFY")
    if authenticator.isTokenExpired():
        authenticator.refreshToken()

    # Main Variables
    MP = MainProcessor()
    headers = authenticator.getHeaders()
    counter = 0

    # Looping trough the Rolling Stones dataset...
    while counter < len(rolling_stones_scraped_data):
        # Sleeping for 1 sec to ease up on API calls.
        time.sleep(1)

        # Visuals for Print Statement:
        rank, raw_artist, raw_title, search_type = (
            rolling_stones_scraped_data[counter]["rank"],
            rolling_stones_scraped_data[counter]["artist"],
            rolling_stones_scraped_data[counter]["title"],
            rolling_stones_scraped_data[counter]["type"],
        )
        print(f"#{rank} - {raw_title} by {raw_artist}")

        # Initiating Spotify API Processor object.
        sap = SpotifyApiProcessor(
            raw_artist=raw_artist,
            raw_title=raw_title,
            rs_rank=rank,
            search_type=search_type,
            headers=headers,
            folder_path=folder_path,
        )

        # Fetching Spotify API endpoints and storing data in Main Processor Object.
        sap.fetch_search_api()

        # Search Type Track:
        if search_type == "track":
            track = sap.fetch_get_track_api()
            MP.tracks.append(track)

        if sap.album_id not in MP.albums:
            album = sap.fetch_get_album_api()
            MP.albums.append(album)

        for artist in sap.artists:
            if artist not in MP.artists:
                print(f"New artist: {artist}")
                # s_artist = SpotifyApiProcessor.fetch_get_artist_api(sap, artist)
                s_artist = sap.fetch_get_artist_api(sap, artist)
                MP.artists.append(s_artist)
            else:
                artist_idx = MP.artists.index(artist)
                artist_albums = MP.artists[artist_idx]["albums"]
                if sap.album_id not in artist_albums:
                    print(f"New album {sap.album_id} for artist: {artist}")
                    artist_albums.append(sap.album_id)

        counter += 1

    return MP


if __name__ == "__main__":
    start = datetime.now()

    # Admin
    # load json file here and assign to main.

    # Main Data Processing

    finished = datetime.now()
    print(f"Script finished in: {finished - start}")
