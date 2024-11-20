import json
from dataclasses import asdict, dataclass, fields
from datetime import datetime

import requests


@dataclass
class SearchItem:
    track_id: str
    album_id: str
    artists: list


@dataclass
class DataProcessor:
    def write_as_sql(self) -> str:
        clean_list = []
        for field in fields(self):
            if field.type is list:
                clean_list.append(f"ARRAY {getattr(self, field.name)}")
            elif field.type is str:
                clean_list.append(getattr(self, field.name).replace("'", ""))
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
    release_year: int
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
class Albums(DataProcessor):
    album_id: str
    album_name: str
    rs_rank: int
    # genres: list
    popularity: int
    total_tracks: int
    label: str
    release_year: int
    album_image: str
    external_url: str
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


@dataclass
class Artists(DataProcessor):
    artists_id: str
    artist_name: str
    albums: list
    genres: list
    total_followers: int
    popularity: int
    external_url: str

    # Compare with Other Objects:
    def __eq__(self, other):
        # If type is the same.
        if isinstance(other, Artists):
            if other.artists_id == self.artists_id:
                return True
            else:
                return False
        # If it's a string
        elif isinstance(other, str):
            if other == self.artists_id:
                return True
            else:
                return False
        # Every other just in case.
        else:
            return False


def save_data_to_json(data: list, file_path: str):
    """
    Function to save any scraped API {data} into a given JSON {file_path}.
    """
    with open(file_path, "r+") as jsonFile:
        jsonFile.seek(0)
        json.dump(
            data,
            jsonFile,
            indent=4,
            sort_keys=True,
            ensure_ascii=False,
        )
        jsonFile.truncate()


class SpotifyApiProcessor:
    def __init__(self, raw_artist, raw_title, search_type, rs_rank, headers):
        self.raw_artist = raw_artist
        self.raw_title = raw_title
        self.search_type = search_type
        self.rs_rank = rs_rank
        self.headers = headers
        # self.folder_path = folder_path
        # Store API responses in data list
        self.track_id = None
        self.album_id = None
        self.artists = None
        # self.name = None

    def fetch_search_api(self):
        limit = 5
        search_term = f"{self.raw_artist} {self.raw_title}".replace("’", "")
        url = f"https://api.spotify.com/v1/search?q={search_term}&type={self.search_type}&market=GB&limit={limit}"
        r = requests.get(url=url, headers=self.headers)

        if r.status_code == 200:
            response = r.json()

            if self.search_type == "track":
                self.track_id = response["tracks"]["items"][0]["id"]
                self.album_id = response["tracks"]["items"][0]["album"]["id"]
                self.artists = [
                    artist["id"] for artist in response["tracks"]["items"][0]["artists"]
                ]
            else:
                # self.track_id = None
                self.album_id = response["albums"]["items"][0]["id"]
                self.artists = [
                    artist["id"] for artist in response["albums"]["items"][0]["artists"]
                ]

    def fetch_get_track_api(self) -> Tracks:
        url = f"https://api.spotify.com/v1/tracks/{self.track_id}?market=GB"
        print(f"Fetching: {url}")
        r = requests.get(url=url, headers=self.headers)

        if r.status_code == 429:
            print("Rate limit has reached, quitting...")
            exit()
        elif r.status_code == 200:
            response = r.json()
            name = response["name"]
            track_id = response["id"]
            duration_ms = int(response["duration_ms"])
            explicit = response["explicit"]
            popularity = int(response["popularity"])
            track_number = int(response["track_number"])
            external_urls = response["external_urls"]["spotify"]
            release_year = int(response["album"]["release_date"][:4])

            track = Tracks(
                track_name=name,
                rs_rank=self.rs_rank,
                track_id=track_id,
                artist_ids=self.artists,
                album_id=self.album_id,
                duration_ms=duration_ms,
                is_explicit=explicit,
                popularity=popularity,
                track_number_on_album=track_number,
                external_url=external_urls,
                release_year=release_year,
            )

            return track

    def fetch_get_artist_api(self, artist: str) -> Artists:
        url = f"https://api.spotify.com/v1/artists/{artist}"
        print(f"Fetching: {url}")
        r = requests.get(url=url, headers=self.headers)

        if r.status_code == 429:
            print("Rate limit has reached, quitting...")
            exit()
        elif r.status_code == 200:
            response = r.json()
            artists_id = response["id"]
            artist_name = response["name"]
            genres = response["genres"]
            total_followers = response["followers"]["total"]
            popularity = response["popularity"]
            external_url = response["external_urls"]["spotify"]

            artist = Artists(
                artists_id=artists_id,
                artist_name=artist_name,
                albums=[self.album_id],
                genres=genres,
                total_followers=total_followers,
                popularity=popularity,
                external_url=external_url,
            )

            return artist

    def fetch_get_album_api(self) -> Albums:
        url = f"https://api.spotify.com/v1/albums/{self.album_id}?market=GB"
        print(f"Fetching: {url}")
        r = requests.get(url=url, headers=self.headers)

        if r.status_code == 429:
            print("Rate limit has reached, quitting...")
            exit()
        elif r.status_code == 200:
            response = r.json()
            album_name = response["name"].replace(";", "")
            if self.search_type == "album":
                rs_rank = self.rs_rank
            else:
                rs_rank = ""
            # genres = response["genres"]
            popularity = response["popularity"]
            total_tracks = response["total_tracks"]
            label = response["label"]
            external_url = response["external_urls"]["spotify"]
            release_year = int(response["release_date"][:4])
            album_image = response["images"][0]["url"]
            artist_ids = [artist["id"] for artist in response["artists"]]

            album = Albums(
                album_id=self.album_id,
                album_name=album_name,
                rs_rank=rs_rank,
                # genres=genres,
                popularity=popularity,
                total_tracks=total_tracks,
                label=label,
                external_url=external_url,
                release_year=release_year,
                album_image=album_image,
                artist_ids=artist_ids,
            )

            return album


if __name__ == "__main__":
    start = datetime.now()

    # # Authenticate
    # authenticator = Authenticator("SPOTIFY")
    # if authenticator.isTokenExpired():
    #     authenticator.refreshToken()

    finished = datetime.now()
    print(f"Script finished in: {finished - start}")
