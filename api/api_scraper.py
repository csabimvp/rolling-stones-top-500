import json
import os
from datetime import datetime

from helpers import Authenticator, SpotifyApi


def write_insert_table():
    """
    Function to write INSERT INTO TABLE (columns) (values)
    """
    pass


def save_json(file_name, data, folder_path):
    """
    Function to save scraped API data into a JSON file as backup.
    """
    with open(os.path.join(folder_path, file_name), "r+") as jsonFile:
        jsonFile.seek(0)
        json.dump(
            data,
            jsonFile,
            indent=4,
            sort_keys=True,
            ensure_ascii=False,
        )
        jsonFile.truncate()


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
