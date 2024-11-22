import difflib
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
            returned_names = [item["name"] for item in api_response["tracks"]["items"]]
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
                    item["name"] for item in api_response["albums"]["items"]
                ]
                similarity = [
                    compute_similarity(name, search_term) for name in returned_names
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
        self.track_id, self.album_id, self.artists = self.fetch_search_api(
            search_term=search_term, search_type=self.data_type, headers=headers
        )

        return (self.track_id, self.album_id, self.artists)


class SearchResults:
    def __init__(self):
        self.tracks = list()
        self.albums = dict()  #  key: album_id, value: int(rank)
        self.artists = dict()  # key: artist_id, value: list(albums)
