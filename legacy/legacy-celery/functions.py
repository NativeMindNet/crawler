import csv
import json
import os
from datetime import datetime

from sbvirtualdisplay import Display
from seleniumbase import SB

os.environ['DISPLAY'] = ':99'


def get_platforms_urls():
    # TODO: тут перечисление URL всех платформ
    # TODO: реализовать чтените из конфига или базы данных

    platforms_urls = {
        "qpublic": "https://qpublic.schneidercorp.com",
    }

    return platforms_urls


def save_html(html: str, platform: str, name: str) -> str:
    file_path = f'./storage/{platform}/{name}.html'
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(html)
    print(f'Файл сохранен: {file_path}')
    return file_path


def save_csv(data: dict, platform: str, name: str) -> None:
    file_name = generate_name(platform, name)
    with open(f'./storage/{platform}/{file_name}.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # writer.writerow(data.keys())  # записать заголовки
        writer.writerow(data.values())  # записать данные


def import_to_db(data: dict) -> None:
    # TODO: формируем из словаря data объект и импортируем его в базу
    # TODO: реализовать непосредственный импорт в базу через ORM
    save_csv(data, "qpublic", "qpublic")
    print("Данные импортированы в базу")


def read_json(platform: str, name: str) -> dict:
    with open(f'./storage/{platform}/{name}.json', 'r', encoding='utf-8') as file:
        return json.load(file)


def save_json(data: dict, platform: str, name: str) -> None:
    with open(f'./storage/{platform}/{name}.json', 'w', encoding='utf-8') as file:
        file.write(json.dumps(data))


def scrape_single_url(url: str, headless: bool = False, block_images: bool = False):
    with Display(visible=False, size=(1920, 1080)) as disp:
        print(f'Display is alive: {disp.is_alive()}')

        with SB(uc=True, headless=headless, block_images=block_images) as sb:
            sb.uc_open_with_reconnect(url, 2)
            scraper_pass_challenge(sb)
            scraper_pass_modal(sb)

            html = r"{}".format(sb.get_page_source())
            return html


def make_sites_visited_history(sb: SB):
    sb.uc_open_with_reconnect("https://instagram.com/", 2)
    sb.uc_open_with_reconnect("https://google.com/", 2)
    sb.uc_open_with_reconnect("https://www.x.com/", 2)
    sb.sleep(2)


def scraper_pass_challenge(sb: SB):
    while True:
        sb.uc_gui_click_captcha()
        sb.sleep(1)
        title = str(sb.get_page_title()).lower()
        if "just a moment..." in title:
            print(f"Passing cloudflare challenge")
            continue
        if "qpublic" in title:
            print(f"Opening page: {title}")
            break


def scraper_pass_modal(sb: SB):
    while True:
        try:
            sb.click(selector="[class*='btn btn-primary button-1']", by="css selector", timeout=3)
        except:
            break


def generate_name(platform: str, uid: str) -> str:
    now = datetime.now()
    current_date = now.strftime("%d-%m-%Y")
    return f"{platform}_{current_date}_{uid}"
