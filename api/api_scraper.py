import csv
import json
import os
import pathlib
import time
from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import List

from api_processors import RollingStonesData, SpotifyApiProcessor
from authenticator import Authenticator

"""
Step 1:
- One function to loop trough master data
- fetch search API and store IDs for all of them.
- Save data as JSON, CSV and SQL

Things we need:
#1 Dataclass:
- Store Rolling Stones Data
- Fetch Search API
- Clean Search Result
- Store returned IDs

#2 Dataclass:
- Store all this from #1 in a MasterClass


Step 2:
- Batch query ALL IDs for tracks, artists and albums
- Save data as CSV and SQL

Things we need:
#1 Dataclass:
SpotifyApiProcessor
    - input: list of IDs from Rolling Stones Dataclass
    - batch query all tracks, artists and albums and store data in Tracks, Artist and Album dataclasses

#2 Dataclass:
MainDataProcessor
    - Use SpotifyApiProcessor batch outputs to store data.
"""


class MainDataProcessor:
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
        schema = "rstop500"
        for field in fields(self):
            file_name = os.path.join(sql_folder_path, f"{field.name}.sql")
            baseSql = f"INSERT INTO {schema}.{field.name} {str(tuple(key for key in getattr(self, field.name)[0].get_field_names())).replace("'", "")} VALUES"
            sql_data = [item.write_as_sql() for item in getattr(self, field.name)]

            with open(file_name, "w", newline="") as sqlFile:
                sqlFile.seek(0)
                sqlFile.write(baseSql)
                sqlFile.write("\n")
                for i, row in enumerate(sql_data, start=1):
                    if i != len(sql_data):
                        sqlFile.write("{},\n".format(row))
                    else:
                        sqlFile.write("{};".format(row))

    def save_data_to_json(self, json_folder_path):
        for field in fields(self):
            file_name = os.path.join(json_folder_path, f"{field.name}.json")
            json_data = [item.write_as_dict() for item in getattr(self, field.name)]

            with open(file_name, "w") as jsonFile:
                jsonFile.seek(0)
                json.dump(json_data, jsonFile, indent=4, sort_keys=True)
                jsonFile.truncate()


# Dataclass to store Rolling Stones Master Data.
@dataclass
class RollingStonesMasterData(MainDataProcessor):
    rs_master_data: List[RollingStonesData] = field(default_factory=list)


def enirch_rolling_stones_data(
    rolling_stones_scraped_data: list,
) -> RollingStonesMasterData:
    # Authenticate
    authenticator = Authenticator("SPOTIFY")
    if authenticator.isTokenExpired():
        authenticator.refreshToken()

    # Main Variables
    rolling_stones_master_data = RollingStonesMasterData()
    headers = authenticator.getHeaders()
    counter = 0

    # Looping trough the Rolling Stones dataset...
    while counter < len(rolling_stones_scraped_data):
        rs_data = RollingStonesData(
            raw_artist=rolling_stones_scraped_data[counter]["artist"],
            description=rolling_stones_scraped_data[counter]["description"],
            rank=rolling_stones_scraped_data[counter]["rank"],
            released_year=rolling_stones_scraped_data[counter]["released_year"],
            raw_title=rolling_stones_scraped_data[counter]["title"],
            data_type=rolling_stones_scraped_data[counter]["type"],
            writers=rolling_stones_scraped_data[counter]["writers"],
        )

        rs_data.get_search_results(headers=headers)
        rolling_stones_master_data.rs_master_data.append(rs_data)

    return rolling_stones_master_data


# Dataclass to store Spotify API data.
@dataclass
class SpotifyData(MainDataProcessor):
    tracks: List = field(default_factory=list)
    albums: List = field(default_factory=list)
    artists: List = field(default_factory=list)

    # Method
    # Needs to return SET to only parse unique items with the API


def main_processor(rolling_stones_scraped_data: list) -> MainDataProcessor:

    # Rewrite this to batch query...

    """
    1) Authenticate to Spotify API
    2) Loop trough Rolling Stones Top 500 dataset and Store Spotify API responses in MainDataProcessor Object.
    """

    # Authenticate
    authenticator = Authenticator("SPOTIFY")
    if authenticator.isTokenExpired():
        authenticator.refreshToken()

    # Main Variables
    MDP = SpotifyData()
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
