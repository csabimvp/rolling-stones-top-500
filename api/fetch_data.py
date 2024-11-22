import csv
import json
import os
import pathlib
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime

from authenticator import Authenticator
from processors import RollingStonesItem, SearchResults


class MainDataProcessor:
    def save_data_to_csv(self, csv_file_path, csv_headers, csv_data):
        with open(csv_file_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(csv_data)

    # def save_data_to_csv(self, csv_folder_path):
    #     for field in fields(self):
    #         file_name = os.path.join(csv_folder_path, f"{field.name}.csv")
    #         csv_headers = [
    #             key for key in getattr(self, field.name)[0].get_field_names()
    #         ]
    #         csv_data = [item.write_to_csv() for item in getattr(self, field.name)]

    #         with open(file_name, "w", newline="") as csvfile:
    #             writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
    #             writer.writeheader()
    #             writer.writerows(csv_data)

    def save_data_to_sql(self, sql_folder_path):
        schema = "rstop500"
        for field in fields(self):
            file_name = os.path.join(sql_folder_path, f"{field.name}.sql")
            baseSql = f"INSERT INTO {schema}.{field.name} {str(tuple(key for key in getattr(self, field.name)[0].get_field_names())).replace("'", "")} VALUES"
            sql_data = [item.write_as_sql() for item in getattr(self, field.name)]

            with open(file_name, "w", newline="") as sqlFile:
                sqlFile.seek(0)
                sqlFile.write(baseSql)
                sqlFile.write("\n")
                for i, row in enumerate(sql_data, start=1):
                    if i != len(sql_data):
                        sqlFile.write("{},\n".format(row))
                    else:
                        sqlFile.write("{};".format(row))

    def save_data_to_json(self, json_folder_path):
        for field in fields(self):
            file_name = os.path.join(json_folder_path, f"{field.name}.json")
            json_data = [item.write_as_dict() for item in getattr(self, field.name)]

            with open(file_name, "w") as jsonFile:
                jsonFile.seek(0)
                json.dump(json_data, jsonFile, indent=4, sort_keys=True)
                jsonFile.truncate()


# Dataclass to store Rolling Stones Master Data.
@dataclass
class RollingStonesMasterData(MainDataProcessor):
    rs_master_data: list[RollingStonesItem] = field(default_factory=list)


def spotfiy_search_results(rolling_stones_scraped_data):
    # Authenticate
    authenticator = Authenticator("SPOTIFY")
    if authenticator.isTokenExpired():
        authenticator.refreshToken()

    # Main Variables
    search_results = SearchResults()
    rolling_stones_data = RollingStonesMasterData()
    headers = authenticator.getHeaders()
    counter = 0

    # Looping trough the Rolling Stones dataset...
    while counter < len(rolling_stones_scraped_data):
        rs_item = RollingStonesItem(
            raw_artist=rolling_stones_scraped_data[counter]["artist"],
            description=rolling_stones_scraped_data[counter]["description"],
            rank=rolling_stones_scraped_data[counter]["rank"],
            released_year=rolling_stones_scraped_data[counter]["released_year"],
            raw_title=rolling_stones_scraped_data[counter]["title"],
            data_type=rolling_stones_scraped_data[counter]["type"],
            writers=rolling_stones_scraped_data[counter]["writers"],
        )

        rolling_stones_data.rs_master_data.append(rs_item)

        track_id, album_id, artists = rs_item.get_search_results(headers=headers)

        # Adding Track ID
        if track_id:
            search_results.tracks.append(track_id)

        # Adding Album ID and storing Rank if applicable.
        if album_id not in search_results.albums.keys():
            search_results.albums[album_id] = "NONE"
        else:
            search_results.albums[album_id] = rs_item.rank
            print(f"{album_id} updated with: {rs_item.rank} Rolling Stones rank.")

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
        rolling_stones_scraped_data=rolling_stones_scraped_data[:10]
    )

    # json_data = [item.write_as_dict() for item in rolling_stones_master.rs_master_data]
    csv_data = [elem.write_to_csv() for elem in rolling_stones_master.rs_master_data]
    csv_headers = rolling_stones_master.rs_master_data[0].get_field_names()

    rolling_stones_master.save_data_to_csv(
        os.path.join(data_folder_path, "rolling_stones_master_data.csv"),
        csv_headers=csv_headers,
        csv_data=csv_data,
    )

    print(search_results.tracks)
    print(search_results.albums)
    print(search_results.artists)


if __name__ == "__main__":
    start = datetime.now()
    root_dir_path = pathlib.Path(__file__).parent.parent.resolve()

    main(root_dir_path=root_dir_path)

    finished = datetime.now()
    print(f"Script finished in: {finished - start}")
