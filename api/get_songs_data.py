"""
Calling Spotfiy API endpoint to enrich the Rolling Stones Top 500 dataset.

1) We need API token and headers for every request. Has to live in a seperate Authenticator class
With the API token:
    2) We need Search First to get Spotify IDs
    3) Call get_track API endpoint to fetch track data.

4) Save data locally.
"""

import json
import os
import pathlib

from authenticator import Authenticator
from spotify_api import SpotifyApi
