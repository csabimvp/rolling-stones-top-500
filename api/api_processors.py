import difflib
from dataclasses import asdict, dataclass, fields
from datetime import datetime

import requests


class ApiSearchProcessor:
    def find_best_match(self, api_response: dict) -> tuple:
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

        if self.search_type == "track":
            returned_names = [item["name"] for item in api_response["tracks"]["items"]]
            similarity = [
                compute_similarity(name, self.search_term) for name in returned_names
            ]
            best_match_idx = returned_names.index(similarity.index(max(similarity)))
            track_id = api_response["albums"]["items"][best_match_idx]["id"]
            album_id = api_response["albums"]["items"][best_match_idx]["album"]["id"]
            artists = [
                artist["id"]
                for artist in api_response["albums"]["items"][best_match_idx]["artists"]
            ]
        # Search Term = "album"
        else:
            returned_names = [item["name"] for item in api_response["albums"]["items"]]
            similarity = [
                compute_similarity(name, self.search_term) for name in returned_names
            ]
            best_match_idx = returned_names.index(similarity.index(max(similarity)))
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
            return self.find_best_match(api_response=r.json())


@dataclass
class DataProcessor:
    def write_as_sql(self) -> str:
        clean_list = []
        for field in fields(self):
            if field.type is list:
                clean_list.append(f"ARRAY{getattr(self, field.name)}")
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
class RollingStonesData(ApiSearchProcessor, DataProcessor):
    raw_artist: str
    description: str
    rank: int
    released_year: int
    raw_title: str
    data_type: str
    writers: str

    def get_search_results(self, headers):
        print(f"#{self.rank} - {self.raw_title} by {self.raw_artist}")
        search_term = f"{self.raw_artist} {self.raw_title}".replace("’", "")
        self.track_id, self.album_id, self.artists = self.fetch_search_api(
            search_term=search_term, search_type=self.data_type, headers=headers
        )


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


class SpotifyApiProcessor:
    def __init__(self, raw_artist, raw_title, search_type, rs_rank, headers):
        self.raw_artist = raw_artist
        self.raw_title = raw_title
        self.search_type = search_type
        self.rs_rank = rs_rank
        self.headers = headers
        self.track_id = None
        self.album_id = None
        self.artists = None

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
            uri = response["uri"]

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
                uri=uri,
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
            artist_id = response["id"]
            artist_name = response["name"]
            genres = response["genres"]
            cleaned_genres = [genre.replace("'", "") for genre in genres]
            total_followers = response["followers"]["total"]
            popularity = response["popularity"]
            external_url = response["external_urls"]["spotify"]
            uri = response["uri"]

            artist = Artists(
                artist_id=artist_id,
                artist_name=artist_name,
                albums=[self.album_id],
                genres=cleaned_genres,
                total_followers=total_followers,
                popularity=popularity,
                external_url=external_url,
                uri=uri,
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
                rs_rank = "NULL"
            popularity = response["popularity"]
            total_tracks = response["total_tracks"]
            label = response["label"]
            external_url = response["external_urls"]["spotify"]
            uri = response["uri"]
            release_year = int(response["release_date"][:4])
            album_image = response["images"][0]["url"]
            artist_ids = [artist["id"] for artist in response["artists"]]

            album = Albums(
                album_id=self.album_id,
                album_name=album_name,
                rs_rank=rs_rank,
                popularity=popularity,
                total_tracks=total_tracks,
                label=label,
                external_url=external_url,
                uri=uri,
                release_year=release_year,
                album_image=album_image,
                artist_ids=artist_ids,
            )

            return album


if __name__ == "__main__":
    start = datetime.now()

    finished = datetime.now()
    print(f"Script finished in: {finished - start}")
