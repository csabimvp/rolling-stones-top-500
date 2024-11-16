import os
from datetime import datetime

from api.api_processors import Authenticator, SpotifyApiProcessor


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
        2) Save data to SQL and JSON
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
