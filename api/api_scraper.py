import os
from dataclasses import dataclass
from datetime import datetime
from typing import List

from api.api_processors import Authenticator, SpotifyApiProcessor


# Dataclass to store main datasets.
@dataclass
class AlbumsAndArtists:
    artist_id: str
    albums: List = None


def write_insert_table():
    """
    Function to write INSERT INTO TABLE (columns) (values)
    """
    pass


def main():
    """
    Loop trough Rolling Stones Top 500 raw data.
        1) Fetch Spotify API endpoints
            - Search
            - Get Track
            - Get Albums
            - Get Artists

        2) Somehow track Albums with Artists an append the respective data structures.
            This is handled on the Processor level
        3) Save data to SQL and JSON
    """
    pass


if __name__ == "__main__":
    start = datetime.now()

    # Authenticate
    authenticator = Authenticator("SPOTIFY")
    if authenticator.isTokenExpired():
        authenticator.refreshToken()

    # # Admin

    # Calling Spotify API
    main()

    finished = datetime.now()
    print(f"Script finished in: {finished - start}")
