import json
import os
import pathlib
from datetime import datetime

from authenticator import Authenticator
from processors import RollingStonesItem, RollingStonesMasterData, SearchResults


def spotfiy_search_results(rolling_stones_scraped_data):
    # Authenticate
    authenticator = Authenticator("SPOTIFY")
    if authenticator.isTokenExpired():
        authenticator.refreshToken()

    # Main Variables
    headers = authenticator.getHeaders()
    rolling_stones_data = RollingStonesMasterData()
    search_results = SearchResults(headers=headers)
    counter = 0

    # Looping trough the Rolling Stones dataset...
    while counter < len(rolling_stones_scraped_data):
        rs_item = RollingStonesItem(
            raw_artist=rolling_stones_scraped_data[counter]["artist"],
            description=rolling_stones_scraped_data[counter]["description"],
            rs_rank=rolling_stones_scraped_data[counter]["rank"],
            released_year=rolling_stones_scraped_data[counter]["released_year"],
            raw_title=rolling_stones_scraped_data[counter]["title"],
            data_type=rolling_stones_scraped_data[counter]["type"],
            writers=rolling_stones_scraped_data[counter]["writers"],
        )

        track_id, album_id, artists = rs_item.get_search_results(headers=headers)

        rolling_stones_data.rs_master_data.append(rs_item)

        # Adding Track ID
        if track_id:
            search_results.tracks[track_id] = rs_item.rs_rank

        # Adding Album ID and storing Rank if applicable.
        if album_id not in search_results.albums.keys():
            search_results.albums[album_id] = 0
            # search_results.albums[album_id] = ""
        else:
            search_results.albums[album_id] = rs_item.rs_rank
            print(f"{album_id} updated with: {rs_item.rs_rank} Rolling Stones rank.")

        # Storing Artist ID and capturing respective Album IDs.
        for artist in artists:
            if artist not in search_results.artists.keys():
                search_results.artists[artist] = [album_id]
            else:
                search_results.artists[artist].append(album_id)
                print(f"New album {album_id} added for artist: {artist}")

        counter += 1

    return (rolling_stones_data, search_results)


def main(root_dir_path):
    # Admin
    data_folder_path = os.path.join(root_dir_path, "data")
    sql_folder_path = os.path.join(root_dir_path, "sql")
    rolling_stones_scraped_data_path = os.path.join(
        data_folder_path, "rolling_stones_master_data.json"
    )
    rolling_stones_scraped_data = json.load(
        open(rolling_stones_scraped_data_path, encoding="utf-8")
    )

    rolling_stones_master, search_results = spotfiy_search_results(
        rolling_stones_scraped_data=rolling_stones_scraped_data
    )

    rolling_stones_master.tracks = search_results.fetch_batch_tracks()
    rolling_stones_master.albums = search_results.fetch_batch_albums()
    rolling_stones_master.artists = search_results.fetch_batch_artists()

    rolling_stones_master.save_data_to_csv(csv_folder_path=data_folder_path)
    rolling_stones_master.save_data_to_sql(sql_folder_path=sql_folder_path)


if __name__ == "__main__":
    start = datetime.now()
    root_dir_path = pathlib.Path(__file__).parent.parent.resolve()

    main(root_dir_path=root_dir_path)

    finished = datetime.now()
    print(f"Script finished in: {finished - start}")
