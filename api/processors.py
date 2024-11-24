import csv
import difflib
import json
import os
from dataclasses import asdict, dataclass, field, fields

import requests


class ApiSearchProcessor:
    def find_best_match(self, api_response: dict, search_term: str) -> tuple:
        """
        Finds best returned match for the "Search Term" within the "Names" in the returned list.
        """

        # Source for compute_similarity: https://www.geeksforgeeks.org/python-similarity-metrics-of-strings/
        def compute_similarity(input_string, reference_string):
            diff = difflib.ndiff(input_string, reference_string)
            diff_count = 0
            for line in diff:
                if line.startswith("-"):
                    diff_count += 1
            return 1 - (diff_count / len(input_string))

        if self.data_type == "track":
            returned_names = [
                item["name"] for item in api_response["tracks"]["items"] if item
            ]
            similarity = [
                compute_similarity(name, search_term) for name in returned_names
            ]
            best_match_idx = similarity.index(max(similarity))
            track_id = api_response["tracks"]["items"][best_match_idx]["id"]
            album_id = api_response["tracks"]["items"][best_match_idx]["album"]["id"]
            artists = [
                artist["id"]
                for artist in api_response["tracks"]["items"][best_match_idx]["artists"]
            ]
        # Search Term = "album"
        else:
            if len(api_response["albums"]["items"]) > 1:
                returned_names = [
                    item["name"] for item in api_response["albums"]["items"] if item
                ]
                similarity = [
                    compute_similarity(name, search_term) if name else None
                    for name in returned_names
                ]
                best_match_idx = similarity.index(max(similarity))
            else:
                best_match_idx = 0
            track_id = None
            album_id = api_response["albums"]["items"][best_match_idx]["id"]
            artists = [
                artist["id"]
                for artist in api_response["albums"]["items"][best_match_idx]["artists"]
            ]

        return (track_id, album_id, artists)

    def fetch_search_api(self, search_term, search_type, headers: dict) -> tuple:
        limit = 3
        url = f"https://api.spotify.com/v1/search?q={search_term}&type={search_type}&market=GB&limit={limit}"
        r = requests.get(url=url, headers=headers)
        if r.status_code == 200:
            return self.find_best_match(api_response=r.json(), search_term=search_term)


@dataclass
class DataProcessor:
    def write_as_sql(self) -> str:
        clean_list = []
        for field in fields(self):
            if field.type is list:
                clean_list.append(f"ARRAY{getattr(self, field.name)}")
            elif field.type is str:
                try:
                    clean_list.append(getattr(self, field.name).replace("'", ""))
                except AttributeError as e:
                    print(e)
            else:
                clean_list.append(getattr(self, field.name))

        sql_syntax = tuple(clean_list)
        return str(sql_syntax).replace('"', "")

    def write_as_dict(self) -> dict:
        return asdict(self)

    def write_to_csv(self) -> dict:
        # Replace [] for {} due to SQL import syntax error for array columns.
        keys = (field.name for field in fields(self))
        values = (
            (
                set(getattr(self, field.name))
                if field.type is list
                else getattr(self, field.name)
            )
            for field in fields(self)
        )
        csv_syntax = {k: v for k, v in zip(keys, values)}
        return csv_syntax

    def get_field_names(self) -> list:
        return [field.name for field in fields(self)]


@dataclass
class RollingStonesItem(ApiSearchProcessor, DataProcessor):
    raw_artist: str
    description: str
    rank: int
    released_year: int
    raw_title: str
    data_type: str
    writers: str
    track_id: str = field(default_factory=str)
    album_id: str = field(default_factory=str)
    artists: list = field(default_factory=list)

    def get_search_results(self, headers) -> tuple:
        print(f"#{self.rank} - {self.raw_title} by {self.raw_artist}")
        search_term = f"{self.raw_artist} {self.raw_title}".replace("’", "")
        track_id, album_id, artists = self.fetch_search_api(
            search_term=search_term, search_type=self.data_type, headers=headers
        )

        if track_id:
            self.track_id = track_id

        self.album_id = album_id
        self.artists = artists

        return (self.track_id, self.album_id, self.artists)


@dataclass
class Tracks(DataProcessor):
    track_id: str
    track_name: str
    artist_ids: list
    rs_rank: int
    is_explicit: bool
    popularity: int
    duration_ms: int
    track_number_on_album: int
    external_url: str
    uri: str
    released_year: int
    album_id: str

    # Compare with Other Objects:
    def __eq__(self, other):
        # If type is the same.
        if isinstance(other, Tracks):
            if other.track_id == self.track_id:
                return True
            else:
                return False
        # If it's a string
        elif isinstance(other, str):
            if other == self.track_id:
                return True
            else:
                return False
        # Every other just in case.
        else:
            return False


@dataclass
class Artists(DataProcessor):
    artist_id: str
    artist_name: str
    albums: list
    genres: list
    total_followers: int
    popularity: int
    external_url: str
    uri: str

    # Compare with Other Objects:
    def __eq__(self, other):
        # If type is the same.
        if isinstance(other, Artists):
            if other.artist_id == self.artist_id:
                return True
            else:
                return False
        # If it's a string
        elif isinstance(other, str):
            if other == self.artist_id:
                return True
            else:
                return False
        # Every other just in case.
        else:
            return False


@dataclass
class Albums(DataProcessor):
    album_id: str
    album_name: str
    rs_rank: int
    # genres: list
    popularity: int
    total_tracks: int
    label: str
    released_year: int
    album_image: str
    external_url: str
    uri: str
    artist_ids: list

    # Compare with Other Objects:
    def __eq__(self, other):
        # If type is the same.
        if isinstance(other, Albums):
            if other.album_id == self.album_id:
                return True
            else:
                return False
        # If it's a string
        elif isinstance(other, str):
            if other == self.album_id:
                return True
            else:
                return False
        # Every other just in case.
        else:
            return False


class SearchResults:
    def __init__(self, headers):
        self.tracks = dict()  #  key: track_id, value: int(rank)
        self.albums = dict()  #  key: album_id, value: int(rank)
        self.artists = dict()  # key: artist_id, value: list(albums)
        self.headers = headers

    def split_data_for_batch_processing(self, field_name, max_length):
        data = list(getattr(self, field_name).keys())
        for_batch_processing = list()
        counter = 0
        while counter < len(data):
            split_data = data[counter : counter + max_length]
            for_batch_processing.append(split_data)
            counter += max_length

        return for_batch_processing

    def fetch_batch_tracks(self):
        tracks_data = list()
        batched_data = SearchResults.split_data_for_batch_processing(
            self=self, field_name="tracks", max_length=50
        )

        for batch in batched_data:
            print(f"Fetching {len(batch)} number of Tracks...")
            search_str = ",".join(batch)
            url = f"https://api.spotify.com/v1/tracks?market=GB&ids={search_str}"
            r = requests.get(url=url, headers=self.headers)

            if r.status_code == 200:
                response = r.json()

                for item in response["tracks"]:
                    name = item["name"]
                    track_id = item["id"]
                    rs_rank = self.tracks[track_id]
                    duration_ms = int(item["duration_ms"])
                    explicit = item["explicit"]
                    popularity = int(item["popularity"])
                    track_number = int(item["track_number"])
                    external_urls = item["external_urls"]["spotify"]
                    released_year = int(item["album"]["release_date"][:4])
                    album_id = item["album"]["id"]
                    artists = [artist["id"] for artist in item["artists"]]
                    uri = item["uri"]

                    track = Tracks(
                        track_name=name,
                        rs_rank=rs_rank,
                        track_id=track_id,
                        artist_ids=artists,
                        album_id=album_id,
                        duration_ms=duration_ms,
                        is_explicit=explicit,
                        popularity=popularity,
                        track_number_on_album=track_number,
                        external_url=external_urls,
                        uri=uri,
                        released_year=released_year,
                    )

                    tracks_data.append(track)
        return tracks_data

    def fetch_batch_artists(self):
        artists_data = list()
        batched_data = SearchResults.split_data_for_batch_processing(
            self=self, field_name="artists", max_length=50
        )

        for batch in batched_data:
            print(f"Fetching {len(batch)} number of Artists...")
            search_str = ",".join(batch)
            url = f"https://api.spotify.com/v1/artists?ids={search_str}"
            r = requests.get(url=url, headers=self.headers)

            if r.status_code == 200:
                response = r.json()

                for item in response["artists"]:
                    artist_id = item["id"]
                    artist_name = item["name"]
                    genres = item["genres"]
                    cleaned_genres = [genre.replace("'", "") for genre in genres]
                    total_followers = item["followers"]["total"]
                    popularity = item["popularity"]
                    external_url = item["external_urls"]["spotify"]
                    uri = item["uri"]
                    albums = self.artists[artist_id]

                    artist = Artists(
                        artist_id=artist_id,
                        artist_name=artist_name,
                        albums=albums,
                        genres=cleaned_genres,
                        total_followers=total_followers,
                        popularity=popularity,
                        external_url=external_url,
                        uri=uri,
                    )

                    artists_data.append(artist)
        return artists_data

    def fetch_batch_albums(self):
        albums_data = list()
        batched_data = SearchResults.split_data_for_batch_processing(
            self=self, field_name="albums", max_length=20
        )

        for batch in batched_data:
            print(f"Fetching {len(batch)} number of Albums...")
            search_str = ",".join(batch)
            url = f"https://api.spotify.com/v1/albums?ids={search_str}&market=GB"
            r = requests.get(url=url, headers=self.headers)

            if r.status_code == 200:
                response = r.json()

                for item in response["albums"]:
                    album_name = item["name"].replace(";", "")
                    album_id = item["id"]
                    rs_rank = self.albums[album_id]
                    popularity = item["popularity"]
                    total_tracks = item["total_tracks"]
                    label = item["label"]
                    external_url = item["external_urls"]["spotify"]
                    uri = item["uri"]
                    released_year = int(item["release_date"][:4])
                    album_image = item["images"][0]["url"]
                    artist_ids = [artist["id"] for artist in item["artists"]]

                    album = Albums(
                        album_id=album_id,
                        album_name=album_name,
                        rs_rank=rs_rank,
                        popularity=popularity,
                        total_tracks=total_tracks,
                        label=label,
                        external_url=external_url,
                        uri=uri,
                        released_year=released_year,
                        album_image=album_image,
                        artist_ids=artist_ids,
                    )

                    albums_data.append(album)
        return albums_data


# Data Processor to save Master Data files.
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
                sqlFile.write("{},\n".format(baseSql))
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


# Dataclass to store Master Data.
@dataclass
class RollingStonesMasterData(MainDataProcessor):
    rs_master_data: list[RollingStonesItem] = field(default_factory=list)
    tracks: list[Tracks] = field(default_factory=list)
    albums: list[Albums] = field(default_factory=list)
    artists: list[Artists] = field(default_factory=list)
