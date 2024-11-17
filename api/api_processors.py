import base64
import json
import os
import pathlib
import secrets
import string
import time
from dataclasses import asdict, astuple, dataclass, fields
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
            # Admin for API call.
            auth_client = self.getClientId() + ":" + self.getClientSecret()
            auth_encode = "Basic " + base64.b64encode(auth_client.encode()).decode()
            payload = {
                "grant_type": self.getGrantType(),
                "refresh_token": self.getRefreshToken(),
                # "client_id": self.getClientId(),
                # "code": self.getCode(),
            }
            headers = {"Authorization": auth_encode}
            url = self.getRefreshTokenUrl()

            # Refreshing Token
            r = requests.post(url=url, headers=headers, data=payload)
            if r.status_code == 200:
                response = r.json()
                expires_in = response["expires_in"]
                new_expiry_date = self.today + timedelta(seconds=expires_in)

                # Updating keys
                self.keys["ACCESS_TOKEN"] = response["access_token"]
                self.keys["EXPIRY_DATE"] = new_expiry_date.strftime("%Y-%m-%d %H:%M:%S")
                try:
                    self.keys["SCOPE"] = response["scope"]
                    self.keys["REFRESH_TOKEN"] = response["refresh_token"]
                except:
                    pass
                # Saving to database.
                self.saveJson()
            else:
                print(r)


@dataclass
class SearchItem:
    track_id: str
    album_id: str
    artists: list


@dataclass
class Tracks:
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


@dataclass
class Albums:
    album_id: str
    album_name: str
    rs_rank: int
    genres: list
    popularity: int
    total_tracks: int
    label: str
    external_url: str
    release_year: int
    album_image: str
    artist_id: str


@dataclass
class Artists:
    artists_id: str
    artist_name: str
    albums: list
    genres: list
    total_followers: int
    popularity: int
    external_url: str


def save_data_to_json(data, file_path):
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
    def __init__(self, raw_title, search_type, rs_rank, headers, folder_path):
        self.raw_title = raw_title
        self.search_type = search_type
        self.rs_rank = rs_rank
        self.headers = headers
        self.folder_path = folder_path
        # Store API responses in data list
        self.track_id = None
        self.album_id = None
        self.artists = None
        # self.name = None

    def fetch_search_api(self):
        limit = 5
        url = f"https://api.spotify.com/v1/search?q={self.raw_title}&type={self.search_type}&market=GB&limit={limit}"
        r = requests.get(url=url, headers=self.headers)

        if r.status_code == 200:
            response = r.json()
            self.track_id = response["tracks"]["items"][0]["id"]
            self.album_id = response["tracks"]["items"][0]["album"]["id"]
            self.artists = [
                artist["id"] for artist in response["tracks"]["items"][0]["artists"]
            ].sort()
            # self.name = response["tracks"]["items"][0]["name"]
            return True
        else:
            return False

    def fetch_get_track_api(self):
        url = f"https://api.spotify.com/v1/tracks/{self.track_id}?market=GB"
        print(f"Fetching: {url}")
        r = requests.get(url=url, headers=self.headers)

        if r.status_code == 200:
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
            return asdict(track)
            # return track

    def fetch_get_artist_api(self, artist):
        url = f"https://api.spotify.com/v1/artists/{artist}"
        print(f"Fetching: {url}")
        r = requests.get(url=url, headers=self.headers)

        if r.status_code == 200:
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

            return asdict(artist)
            # return artist

    def fetch_get_album_api(self):
        url = f"https://api.spotify.com/v1/albums/{self.album_id}?market=GB"
        print(f"Fetching: {url}")
        r = requests.get(url=url, headers=self.headers)

        if r.status_code == 200:
            response = r.json()
            album_name = response["name"]
            rs_rank = ""
            genres = response["genres"]
            popularity = response["popularity"]
            total_tracks = response["total_tracks"]
            label = response["label"]
            external_url = response["external_urls"]["spotify"]
            release_year = int(response["release_date"][:4])
            album_image = response["images"][0]["url"]
            artist_id = response["artists"][0]["id"]

            album = Albums(
                album_id=self.album_id,
                album_name=album_name,
                rs_rank=rs_rank,
                genres=genres,
                popularity=popularity,
                total_tracks=total_tracks,
                label=label,
                external_url=external_url,
                release_year=release_year,
                album_image=album_image,
                artist_id=artist_id,
            )

            return asdict(album)
            # return artist

    def all_contributed_artists(self):
        """
        Load JSON to get already saved artist list.
        Check if Artist is already saved or not.
        - If Yes, check if the album is already added to the artist's album list or not.
        - If No, we need to call the Get Artist API and add the Artist to the already saved ones.
        Then save the data to JSON.
        """
        file_name = "artists.json"
        file_path = os.path.join(self.folder_path, file_name)

        try:
            artists_saved = json.load(open(file_path))
        except Exception as e:
            if e.__class__.__name__ == "JSONDecodeError":
                artists_saved = dict()

        for artist in self.artists:
            if artist not in artists_saved.keys():
                print(f"New artist: {artist}")
                s_artist = SpotifyApiProcessor.fetch_get_artist_api(self, artist)
                artists_saved[s_artist["artists_id"]] = s_artist
                save_data_to_json(data=artists_saved, file_path=file_path)
                print(f"Saving data to {file_path}...")
            else:
                artist_albums = artists_saved[artist]["albums"]
                if self.album_id not in artist_albums:
                    print(f"New album {self.album_id} for artist: {artist}")
                    artist_albums.append(self.album_id).sort()
                    save_data_to_json(data=artists_saved, file_path=file_path)
                    print(f"Saving data to {file_path}...")


def main(folder_path):
    file_name = "rolling_stones_top_500_songs.json"
    scraped_data = json.load(open(os.path.join(folder_path, file_name)))
    spotify_tracks_data = list()
    spotify_albums_data = list()
    counter = 0
    while counter < len(scraped_data):
        # Sleeping for 1 sec to ease up on API calls.
        time.sleep(1)

        rank, title = scraped_data[counter]["rank"], scraped_data[counter]["title"]
        print(f"#{rank} - {title}")

        s = SpotifyApiProcessor(
            raw_title=title,
            rs_rank=rank,
            search_type="track",
            headers=authenticator.getHeaders(),
            folder_path=folder_path,
        )

        s.fetch_search_api()
        track = s.fetch_get_track_api()
        album = s.fetch_get_album_api()
        s.all_contributed_artists()
        spotify_tracks_data.append(track)
        spotify_albums_data.append(album)

        # Save data to JSON after every 25 API calls.
        if counter % 25 == 0 or counter == 499:
            # Save data to JSON.
            print(f"Saving data to {folder_path}...")
            save_data_to_json(
                data=spotify_tracks_data,
                file_path=os.path.join(folder_path, "spotify_top_500_songs.json"),
            )
            save_data_to_json(
                data=spotify_albums_data,
                file_path=os.path.join(folder_path, "albums.json"),
            )

        counter += 1


if __name__ == "__main__":
    start = datetime.now()

    # Authenticate
    authenticator = Authenticator("SPOTIFY")
    if authenticator.isTokenExpired():
        authenticator.refreshToken()

    # # Admin
    dir_path = pathlib.Path(__file__).parent.parent.resolve()
    folder_path = os.path.join(dir_path, "data")

    # Calling Spotify API
    main(folder_path=folder_path)

    finished = datetime.now()
    print(f"Script finished in: {finished - start}")
