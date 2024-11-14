import json
import os
import pathlib
import secrets
import string
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

import requests


class Authenticator:
    def loadJson(path=None, account=None):
        jsonFile = json.load(open(path, "r"))
        return jsonFile[account]

    def __init__(self, account):
        self.account = account
        self.path = "/home/csabimvp/code/rolling-stones-top-500/assets/credentials.json"
        self.today = datetime.now()
        self.keys = Authenticator.loadJson(path=self.path, account=self.account)

    def getClientId(self):
        return self.keys["CLIENT_ID"]

    def getClientSecret(self):
        return self.keys["CLIENT_SECRET"]

    def getCode(self):
        return self.keys["CODE"]

    def getAccessToken(self):
        return self.keys["ACCESS_TOKEN"]

    def getExpiryDate(self):
        return self.keys["EXPIRY_DATE"]

    def getGrantType(self):
        return self.keys["GRANT_TYPE"]

    def getRefreshToken(self):
        return self.keys["REFRESH_TOKEN"]

    def getRefreshTokenUrl(self):
        return self.keys["TOKEN_URL"]

    def getHeaders(self):
        headers = {
            "Authorization": f"Bearer {self.getAccessToken()}",
            "Content-Type": "application/json",
        }
        return headers

    def requestAccessCode(self):
        def generate_state(lenght=50):
            characters = string.ascii_letters + string.digits
            result_str = "".join(secrets.choice(characters) for i in range(lenght))
            return result_str

        state = generate_state()
        client_id = self.getClientId()
        redirect_uri = "https://csabakeller.com/api/webscrapers/authenticate/"
        scope = (
            "user-top-read"
            + "%20"
            + "user-read-recently-played"
            + "%20"
            + "user-read-email"
        )
        url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}&state={state}"
        return print(url)

    def requestAccessToken(self):
        url = "https://accounts.spotify.com/api/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.getClientId(),
            "client_secret": self.getClientSecret(),
            "redirect_uri": "https://csabakeller.com/api/webscrapers/authenticate/",
            "code": self.getCode(),
        }
        r = requests.post(url=url, data=payload).json()
        print(r)
        expires_in = r["expires_in"]
        new_expiry_date = self.today + timedelta(seconds=expires_in)

        # Updating keys
        self.keys["ACCESS_TOKEN"] = r["access_token"]
        self.keys["EXPIRY_DATE"] = new_expiry_date.strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.keys["SCOPE"] = r["scope"]
            self.keys["REFRESH_TOKEN"] = r["refresh_token"]
        except:
            pass
        # Saving to database.
        self.saveJson()

    def isTokenExpired(self):
        expiryDate = datetime.strptime(self.keys["EXPIRY_DATE"], "%Y-%m-%d %H:%M:%S")
        if expiryDate < self.today:
            return True

    def saveJson(self):
        with open(self.path, "r+") as jsonFile:
            data = json.load(jsonFile)
            data[self.account] = self.keys
            jsonFile.seek(0)
            json.dump(data, jsonFile, indent=4, sort_keys=True)
            jsonFile.truncate()

    def refreshToken(self):
        isTokenExpired = self.isTokenExpired()
        if isTokenExpired:
            payload = {
                "grant_type": self.getGrantType(),
                "client_id": self.getClientId(),
                "code": self.getCode(),
                "refresh_token": self.getRefreshToken(),
            }
            url = self.getRefreshTokenUrl()
            r = requests.post(url=url, data=payload).json()
            print(r)
            expires_in = r["expires_in"]
            new_expiry_date = self.today + timedelta(seconds=expires_in)

            # Updating keys
            self.keys["ACCESS_TOKEN"] = r["access_token"]
            self.keys["EXPIRY_DATE"] = new_expiry_date.strftime("%Y-%m-%d %H:%M:%S")
            try:
                self.keys["SCOPE"] = r["scope"]
                self.keys["REFRESH_TOKEN"] = r["refresh_token"]
            except:
                pass
            # Saving to database.
            self.saveJson()


@dataclass
class SearchItem:
    track_id: str
    album_id: str
    artists: list


@dataclass
class Tracks:
    name: str
    track_id: str
    artists: list
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
    artists: list
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
    def __init__(self, raw_title, search_type, headers):
        self.raw_title = raw_title
        self.search_type = search_type
        self.headers = headers
        # Store API responses in data list
        self.track_id = None
        self.album_id = None
        self.artists = None
        self.name = None

    def fetch_search_api(self):
        url = f"https://api.spotify.com/v1/search?q={self.raw_title}&type={self.search_type}&market=GB"
        r = requests.get(url=url, headers=self.headers)

        # We need to check the returned list against the query, because we may not be looking at the 0th item,

        if r.status_code == 200:
            response = r.json()
            self.track_id = response["tracks"]["items"][0]["id"]
            self.album_id = response["tracks"]["items"][0]["album"]["id"]
            self.artists = [
                artist["id"] for artist in response["tracks"]["items"][0]["artists"]
            ]
            self.name = response["tracks"]["items"][0]["name"]
            return True
        else:
            return False

    def fetch_get_track_api(self):
        url = f"https://api.spotify.com/v1/tracks/{self.track_id}?market=GB"
        r = requests.get(url=url, headers=self.headers)

        if r.status_code == 200:
            response = r.json()
            name = response["name"]
            track_id = response["id"]
            # album_id = response["album"]["id"]
            duration_ms = int(response["duration_ms"])
            explicit = response["explicit"]
            popularity = int(response["popularity"])
            track_number = int(response["track_number"])
            external_urls = response["external_urls"]

            track = Tracks(
                name=name,
                track_id=track_id,
                artists=self.artists,
                album_id=self.album_id,
                duration_ms=duration_ms,
                explicit=explicit,
                popularity=popularity,
                track_number=track_number,
                external_urls=external_urls,
            )
            # return track
            return asdict(track)

    def fetch_get_artist_api(self):
        # Store API response in the respective dataclass
        return print("Api called!")

    def fetch_get_album_api(self):
        # Store API response in the respective dataclass
        return print("Api called!")


if __name__ == "__main__":
    # Authenticate
    authenticator = Authenticator("SPOTIFY")
    # authenticator.requestAccessCode()
    # authenticator.requestAccessToken()

    # # Admin
    dir_path = pathlib.Path(__file__).parent.parent.resolve()
    file_name = "rolling_stones_top_500_songs"
    json_file_name = f"{file_name}.json"
    file_path = os.path.join(dir_path, "data", json_file_name)

    # Calling Spotify API
    data = json.load(open(file_path))
    for item in data[:10]:
        print(item["title"])

        # Check if Token still valid:
        isTokenExpired = authenticator.isTokenExpired()
        if isTokenExpired:
            authenticator.refreshToken()

        s = SpotifyApi(
            raw_title=item["title"],
            search_type="track",
            headers=authenticator.getHeaders(),
        )

        s.fetch_search_api()
        track = s.fetch_get_track_api()
        print(track)
