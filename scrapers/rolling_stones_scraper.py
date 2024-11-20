import re
from dataclasses import dataclass, field
from typing import List

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
    type: str


@dataclass
class RollingStonesData:
    articles: List[ArticleData] = field(default_factory=list)


class RollingStonesScraper:
    def __init__(self, url: str, type: str, next_button_xpaths: list):
        self.url = url
        self.type = type
        self.next_button_xpaths = next_button_xpaths
        self.options = webdriver.ChromeOptions()

    def parse_page_content(self, page_content):
        soup = BeautifulSoup(page_content, "html.parser")
        articles = soup.find_all("div", {"class": "c-gallery-vertical__slide-wrapper"})
        rolling_stones_data = RollingStonesData()

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
                description = UnicodeDammit(
                    desc.strip(), ["windows-1252"]
                ).unicode_markup
            except AttributeError:
                description = ""

            if self.type == "track":
                rld_year = item.find("div", {"class": "rs-list-item--year"}).get_text()
                released_year = int(rld_year[:4])
                credited = item.find(
                    "div", {"class": "rs-list-item--credits"}
                ).get_text()
                writers = credited.split(":")[1].strip()
            else:
                credited = item.find(
                    "div", {"class": "c-gallery-vertical-album__subtitle"}
                ).get_text()

                try:
                    released_year = int(credited.split(",")[1].strip())
                    writers = credited.split(",")[0].strip()
                except IndexError:
                    released_year = 2005
                    writers = "EMI Manhattan"
                except ValueError:
                    released_year = int(credited.split(",")[2].strip())
                    writers = "EMI Manhattan"

            article = ArticleData(
                rank=rank,
                artist=artist,
                title=title,
                released_year=released_year,
                writers=writers,
                description=description,
                type=type,
            )

            rolling_stones_data.articles.append(article)

        return rolling_stones_data

    async def navigate_page(self):
        rolling_stones_data = RollingStonesData()
        async with webdriver.Chrome(options=self.options) as driver:
            # Start Chrome
            await driver.get(self.url, wait_load=True)
            await driver.sleep(2)

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
                page_content = RollingStonesScraper.parse_page_content(
                    page_content=page
                )
                rolling_stones_data.articles.extend(page_content)
                await driver.sleep(1)

                # Go to Next Page and start over the process.
                if page_counter >= 1:
                    next_button_xpath = self.next_button_xpaths[1]
                else:
                    next_button_xpath = self.next_button_xpaths[0]

                try:
                    next_button = await driver.find_element(
                        By.XPATH, next_button_xpath, timeout=5
                    )
                    await next_button.click()
                    print("Next Page button found and clicked!.")
                except:
                    pass

                page_counter += 1

        return rolling_stones_data
