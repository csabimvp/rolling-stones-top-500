import asyncio
import json
import os
import pathlib
import re
from dataclasses import asdict, dataclass

from bs4 import BeautifulSoup, UnicodeDammit
from selenium_driverless import webdriver
from selenium_driverless.types.by import By


@dataclass
class ArticleData:
    rank: int
    artist: str
    title: str
    released_year: int
    writers: str
    description: str


def save_json(data, file_path):
    with open(file_path, "r+", encoding="utf-8") as jsonFile:
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4, sort_keys=True, ensure_ascii=False)
        jsonFile.truncate()


def parse_page_content(page_content):
    soup = BeautifulSoup(page_content, "html.parser")
    articles = soup.find_all("div", {"class": "c-gallery-vertical__slide-wrapper"})
    data = list()

    for item in articles:
        title = item.find("h2").get_text()
        artist = title.split(",")[0].strip()
        title = re.sub(r"[^a-zA-Z0-9]+", " ", title.split(",")[1]).strip()
        # title = UnicodeDammit(title.split(",")[1], ["windows-1252"]).unicode_markup
        album_number = item.find(
            "span", {"class": "c-gallery-vertical-album__number"}
        ).get_text()
        rank = int(album_number)

        try:
            desc = item.find("p").get_text()
            # description = re.sub(r"[^a-zA-Z0-9]+", " ", desc.strip())
            description = UnicodeDammit(desc.strip(), ["windows-1252"]).unicode_markup
        except AttributeError:
            description = ""

        rld_year = item.find("div", {"class": "rs-list-item--year"}).get_text()
        released_year = int(rld_year[:4])
        credited = item.find("div", {"class": "rs-list-item--credits"}).get_text()
        writers = credited.split(":")[1].strip()

        article = ArticleData(
            rank=rank,
            artist=artist,
            title=title,
            released_year=released_year,
            writers=writers,
            description=description,
        )
        data.append(asdict(article))

    return data


async def main(base_url, file_path):
    data = list()
    options = webdriver.ChromeOptions()
    next_button_xpaths = [
        "/html/body/div[4]/main/div[3]/article/div/div[1]/div[1]/div/div[3]/div[2]/a",
        "/html/body/div[4]/main/div[3]/article/div/div[1]/div[1]/div/div[3]/div[3]/a",
    ]

    async with webdriver.Chrome(options=options) as driver:
        # Start Chrome
        await driver.get(base_url, wait_load=True)
        await driver.sleep(2)

        # Deal with Pop Up window:
        # elem = await driver.find_element(By.XPATH, "/html/body/div[5]/div/div/button")
        # await elem.click()
        # print("Pop Up Window button found and clicked!")

        # Parse trough the pages
        page_counter = 0
        while page_counter < 10:
            print(f"Pages scraped: {page_counter}")
            # Deal with Pop Up window:
            try:
                elem = await driver.find_element(
                    By.XPATH, "/html/body/div[5]/div/div/button", timeout=5
                )
                await elem.click()
                print("Pop Up Window button found and clicked!")
            except:
                print("No Pop Up Window, carry on...")
                pass

            await driver.sleep(1)
            await driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            # Get page HTML to parse
            page = await driver.page_source
            page_content = parse_page_content(page_content=page)
            data.extend(page_content)
            await driver.sleep(1)

            # Go to Next Page and start over the process.
            if page_counter >= 1:
                next_button_xpath = next_button_xpaths[1]
            else:
                next_button_xpath = next_button_xpaths[0]

            try:
                next_button = await driver.find_element(
                    By.XPATH, next_button_xpath, timeout=5
                )
                await next_button.click()
                print("Next Page button found and clicked!.")
            except:
                pass

            page_counter += 1

    # Save data to JSON.
    print(f"Saving data to {file_path}...")
    save_json(data=data, file_path=file_path)


if __name__ == "__main__":
    dir_path = pathlib.Path(__file__).parent.resolve()
    base_urls = [
        (
            "rolling_stones_top_500_songs",
            "https://www.rollingstone.com/music/music-lists/best-songs-of-all-time-1224767/",
        ),
        # (
        #     "rolling_stones_top_500_albums",
        #     "https://www.rollingstone.com/music/music-lists/best-albums-of-all-time-1062063/",
        # ),
    ]
    for url in base_urls:
        file_name, base_url = url
        json_file_name = f"{file_name}_data.json"
        file_path = os.path.join(dir_path, "data", json_file_name)
        asyncio.run(main(base_url=base_url, file_path=file_path))
