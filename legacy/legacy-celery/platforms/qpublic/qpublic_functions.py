import os
import re
import time

# from pyvirtualdisplay import Display
from sbvirtualdisplay import Display
from seleniumbase import SB
from bs4 import BeautifulSoup

from celery_app import app
from functions import scraper_pass_modal, save_json, scraper_pass_challenge, make_sites_visited_history

os.environ['DISPLAY'] = ':99'


# with SB(uc=True, headless=False, headless=headless, block_images=block_images) as sb:

@app.task
def qpublic_scrape_counties_urls_task(url: str) -> dict:
    counties_urls = {}

    with Display(visible=False, size=(1920, 1080)) as disp:
        print(f'Display is alive: {disp.is_alive()}')

        with SB(uc=True, headless=False) as sb:
            make_sites_visited_history(sb)
            sb.uc_open_with_reconnect(url, 2)
            scraper_pass_challenge(sb)

            scraper_pass_modal(sb)

            # by или selector: 'css selector', 'link text', 'partial link text', 'name', 'xpath', 'id', 'tag name', 'class name'

            area_menu_input = sb.find_element("areaMenuButton", by="id")
            state_groups = sb.find_elements("state-group", by="class name")

            for state_group in state_groups:
                if state_group.get_attribute('aria-labelledby') == "mru-group":
                    continue

                counties = state_group.find_elements(value="dropdown-option", by="class name")

                for county in counties:
                    if county.get_attribute("id") == "mru-group":
                        continue

                    area_menu_input.click()
                    county.click()
                    county_name = sb.get_text("areaMenuButton", by="id")
                    county_url = sb.find_element("track-mru", by="class name").get_attribute("href")
                    print(f"County URL: {county_url}")
                    counties_urls[county_name] = county_url

                    # 18.02.2025: Тест
                    if county_name == "Crawford County, AR":
                        return {county_name: county_url}

    # 18.02.2025: Отключаем для теста
    # return counties_urls


@app.task
def qpublic_get_all_parcels_urls_task(counties_urls: dict) -> list:
    all_counties_parcels_urls = []

    with Display(visible=False, size=(1920, 1080)) as disp:
        print(f'Display is alive: {disp.is_alive()}')

        with SB(uc=True, headless=False) as sb:
            for name, url in counties_urls.items():
                county_parcels_urls = qpublic_get_county_parcels_urls_task(sb, url)
                all_counties_parcels_urls.extend(county_parcels_urls)

    return all_counties_parcels_urls


@app.task
def qpublic_get_county_parcels_urls_task(sb: SB, url: str) -> list:
    county_parcels_urls = []

    try:
        sb.uc_open_with_reconnect(url, 2)
        scraper_pass_challenge(sb)
        scraper_pass_modal(sb)

        sb.js_click_if_visible(selector="[class*='tt-upm-address-search-btn']", by="css selector", timeout=3)
        sb.js_click_if_visible(selector="[id*='_ctl01_btnSearch']", by="css selector", timeout=3)
        scraper_pass_modal(sb)

        urls = sb.find_elements(selector="[id*='_lnkParcelID']", by="css selector")

        if not len(urls) > 0:
            raise Exception("Не удалось получить список parcels")

        for parcel_url in urls:
            county_parcels_urls.append(parcel_url.get_attribute("href"))

        # print(f"{name} -> OK")

    except Exception as e:
        print(f"{url} -> Error")
        print(e)
        # error_urls.append(url)

    return county_parcels_urls


@app.task
def qpublic_parse_single_html_task(html: str) -> dict:
    doc = BeautifulSoup(html, "html.parser")

    info_table = doc.find(class_=re.compile("tabular-data-two-column"))
    parcel_id = info_table.find(id=re.compile("_lblParcelID")).text
    owner = doc.find(id=re.compile("ctlBodyPane_ctl01_ctl00_lblName")).text
    site_address = doc.find(id=re.compile("InfoPane2_lnkWebsite")).attrs["href"]
    legal_description = info_table.find(id=re.compile("_lblLegalDescription")).text
    property_tax_account = info_table.find(id=re.compile("_lblPropertyID")).text

    tax_table = doc.find(id=re.compile("_grdValuation"))
    total_values_rows = tax_table.find_all(class_=re.compile("double-total-line"))
    total_due_amount = total_values_rows[2].find_all(class_=re.compile("value-column"))[0].text
    last_year_due_amount = total_values_rows[1].find_all(class_=re.compile("value-column"))[0].text

    data = {
        "parcel_id": parcel_id,
        "owner": owner,
        "site_address": site_address,
        "legal_description": legal_description,
        "property_tax_account": property_tax_account,
        "total_due_amount": total_due_amount,
        "last_year_due_amount": last_year_due_amount,
    }

    return data
