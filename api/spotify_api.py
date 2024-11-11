from dataclasses import dataclass

# import requests


@dataclass
class SearchItem:
    track_id: str
    album_id: str
    artists_id: list


@dataclass
class Tracks:
    name: str
    track_id: str
    artists_id: list
    album_id: str
    duration_ms: int
    explicit: bool
    popularity: int
    track_number: int
    external_urls: str


@dataclass
class Albums:
    name: str
    album_id: str
    artists_id: list
    total_tracks: int
    album_image: str
    release_date: str
    genres: list
    popularity: int
    external_urls: str
    label: str


@dataclass
class Artists:
    name: str
    artists_id: str
    total_followers: int
    genres: list
    popularity: int
    external_urls: str


class SpotifyApi:
    def __init__(self, raw_title, api_token):
        self.raw_title = raw_title
        self.api_token = api_token
        # Store API responses in data list
        self.data = list()

    def fetch_search_api(self):
        # Store API response in the respective dataclass
        return print("Api called!")

    def fetch_get_track_api(self):
        # Store API response in the respective dataclass
        return print("Api called!")

    def fetch_get_artist_api(self):
        # Store API response in the respective dataclass
        return print("Api called!")

    def fetch_get_album_api(self):
        # Store API response in the respective dataclass
        return print("Api called!")
