import csv
import json
import os
import pathlib
import time
from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import List

from api_processors import SpotifyApiProcessor
from authenticator import Authenticator


# Dataclass to store main datasets.
@dataclass
class MainDataProcessor:
    tracks: List = field(default_factory=list)
    albums: List = field(default_factory=list)
    artists: List = field(default_factory=list)

    def save_data_to_csv(self, csv_folder_path):
        for field in fields(self):
            file_name = os.path.join(csv_folder_path, f"{field.name}.csv")
            csv_headers = [
                key for key in getattr(self, field.name)[0].get_field_names()
            ]
            csv_data = [item.write_to_csv() for item in getattr(self, field.name)]

            with open(file_name, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
                writer.writeheader()
                writer.writerows(csv_data)

    def save_data_to_sql(self, sql_folder_path):
        for field in fields(self):
            file_name = os.path.join(sql_folder_path, f"{field.name}.sql")
            baseSql = f"INSERT INTO {field.name} {str(tuple(key for key in getattr(self, field.name)[0].get_field_names())).replace("'", "")} VALUES"
            sql_data = [item.write_as_sql() for item in getattr(self, field.name)]

            with open(file_name, "w", newline="") as sqlFile:
                sqlFile.seek(0)
                sqlFile.write(baseSql)
                sqlFile.write("\n")
                for i, row in enumerate(sql_data):
                    if i != len(sql_data):
                        sqlFile.write("{},\n".format(row))
                    else:
                        sqlFile.write("{};".format(row))


def main_processor(rolling_stones_scraped_data: list) -> MainDataProcessor:
    """
    1) Authenticate to Spotify API
    2) Loop trough Rolling Stones Top 500 dataset and Store Spotify API responses in MainDataProcessor Object.
    """

    # Authenticate
    authenticator = Authenticator("SPOTIFY")
    if authenticator.isTokenExpired():
        authenticator.refreshToken()

    # Main Variables
    MDP = MainDataProcessor()
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
            # folder_path=folder_path,
        )

        # Fetching Spotify API endpoints and storing data in Main Processor Object.
        sap.fetch_search_api()

        # Search Type Track:
        if search_type == "track":
            track = sap.fetch_get_track_api()
            MDP.tracks.append(track)

        if sap.album_id not in MDP.albums:
            album = sap.fetch_get_album_api()
            MDP.albums.append(album)
        else:
            album_idx = MDP.albums.index(sap.album_id)
            MDP.albums[album_idx].rs_rank = sap.rs_rank
            print(f"{sap.album_id} updated with: {sap.rs_rank} Rolling Stones rank.")

        for artist in sap.artists:
            if artist not in MDP.artists:
                print(f"New artist: {artist}")
                s_artist = SpotifyApiProcessor.fetch_get_artist_api(sap, artist)
                MDP.artists.append(s_artist)
            else:
                artist_idx = MDP.artists.index(artist)
                artist_albums = MDP.artists[artist_idx].albums
                if sap.album_id not in artist_albums:
                    print(f"New album {sap.album_id} for artist: {artist}")
                    artist_albums.append(sap.album_id)

        counter += 1

    return MDP


def main(root_folder_path):
    # Admin
    data_folder_path = os.path.join(root_folder_path, "data")
    sql_folder_path = os.path.join(root_folder_path, "sql")
    rolling_stones_scraped_data_path = os.path.join(
        data_folder_path, "rolling_stones_master_data.json"
    )
    rolling_stones_scraped_data = json.load(open(rolling_stones_scraped_data_path))

    # Main Data Processing
    main_data_processor = main_processor(
        rolling_stones_scraped_data=rolling_stones_scraped_data
    )
    main_data_processor.save_data_to_csv(csv_folder_path=data_folder_path)
    print(f"File was saved: {data_folder_path}")

    main_data_processor.save_data_to_sql(sql_folder_path=sql_folder_path)
    print(f"File was saved: {sql_folder_path}")


if __name__ == "__main__":
    start = datetime.now()
    root_folder_path = pathlib.Path(__file__).parent.parent.resolve()

    main(root_folder_path=root_folder_path)

    finished = datetime.now()
    print(f"Script finished in: {finished - start}")
