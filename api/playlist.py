# Step 1:
# Create Playlist
# https://developer.spotify.com/documentation/web-api/reference/create-playlist
# {
#     "name": "New Playlist",
#     "description": "New playlist description",
#     "public": False
# }

# Step 2:
# Add Items to the Playlist
# https://developer.spotify.com/documentation/web-api/reference/add-tracks-to-playlist
# For example, to insert the items in the first position: position=0; to insert the items in the third position: position=2.
# A maximum of 100 items can be added in one request.

import difflib

from authenticator import Authenticator
from processors import RollingStonesItem

auth = Authenticator("SPOTIFY")
auth.refreshToken()
headers = auth.getHeaders()


def compute_similarity(input_string, reference_string):
    diff = difflib.ndiff(input_string, reference_string)
    diff_count = 0
    for line in diff:
        if line.startswith("-"):
            diff_count += 1
    return 1 - (diff_count / len(input_string))


test = RollingStonesItem(
    raw_artist="Beyonce",
    description="",
    rs_rank=12,
    released_year=11,
    raw_title="Renaissance",
    data_type="album",
    writers="",
)

track_id, album_id, artists = test.get_search_results(headers=headers)

print(artists)
