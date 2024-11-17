import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from api.api_processors import Authenticator, SpotifyApiProcessor


# Dataclass to store main datasets.
@dataclass
class MainProcessor:
    albums: List = []
    tracks: List = []
    artists: Dict = {}

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
        rank, title = (
            rolling_stones_scraped_data[counter]["rank"],
            rolling_stones_scraped_data[counter]["title"],
        )
        print(f"#{rank} - {title}")

        # Initiating Spotify API Processor object.
        sap = SpotifyApiProcessor(
            raw_title=title,
            rs_rank=rank,
            search_type="track",
            headers=headers,
            folder_path=folder_path,
        )

        # Fetching Spotify API endpoints and storing data in Main Processor Object.
        sap.fetch_search_api()
        track = sap.fetch_get_track_api()
        album = sap.fetch_get_album_api()
        MP.tracks.append(track)
        MP.albums.append(album)

        for artist in sap.artists:
            if artist not in MP.artists.keys():
                print(f"New artist: {artist}")
                s_artist = SpotifyApiProcessor.fetch_get_artist_api(sap, artist)
                MP.artists[s_artist["artists_id"]] = s_artist
            else:
                artist_albums = MP.artists[artist]["albums"]
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
