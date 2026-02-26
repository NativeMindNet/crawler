import json
import logging
from datetime import datetime

from celery import Celery, chain, group
from celery_app import app
from functions import get_platforms_urls, save_html, save_csv, save_json, import_to_db, scrape_single_url, generate_name
from platforms.qpublic.qpublic_functions import qpublic_get_all_parcels_urls_task, qpublic_scrape_counties_urls_task, \
    qpublic_parse_single_html_task

#  -----------------------------------------------------------------------------------------
#   Конфигурация
#  -----------------------------------------------------------------------------------------

app.conf.update(
    timezone='Europe/Moscow',
    enable_utc=True,
    # result_backend = 'db+sqlite:///results.db',
    result_backend='redis://localhost:6379/0',  # результаты задач хранятся в Redis
    result_expires=3600 * 24 * 30,  # результаты задач хранятся 30 дней
    task_annotations={'*': {'rate_limit': '5/m'}}
    # ограничение скорости выполнения 2 задач в минуту
)

app.autodiscover_tasks()

logging.basicConfig(level=logging.DEBUG, filename="tasks.log", filemode="a")


#  -----------------------------------------------------------------------------------------
#   Периодические задачи
#  -----------------------------------------------------------------------------------------

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    pass

    # Вызывает run_scraping_chain() каждые 30 минут
    # sender.add_periodic_task(30.0 * 60, run_single_url_chain(), name='Запуск цепочки скрапинга', expires=30.0 * 60)

    # Пример вызова каждый Понедельник в 7:30 утра
    # sender.add_periodic_task(
    #     crontab(hour=7, minute=30, day_of_week=1),
    #     test.s('Happy Mondays!'),
    # )


#   -----------------------------------------------------------------------------------------
#   Цепочки задач
#   -----------------------------------------------------------------------------------------

#
#   QPublic
#


@app.task
def qpublic_main_chain():
    url = get_platforms_urls()["qpublic"]

    counties_urls = qpublic_scrape_counties_urls_task.s(url).apply_async().get()
    all_parcels_urls = qpublic_get_all_parcels_urls_task.s(counties_urls).apply_async().get()

    name = generate_name("qpublic", "all_parcels_urls")
    save_json(all_parcels_urls, "qpublic", name)

    # !!! Урезаем количество url до 10 для теста !!!
    all_parcels_urls = all_parcels_urls[:10]

    group(qpublic_single_url_chain.s(url) for url in all_parcels_urls)()


@app.task
def qpublic_single_url_chain(url: str):
    platform = "qpublic"
    parcel_id = url.split("KeyValue=")[-1]
    unique_name = generate_name(platform, parcel_id)

    chain(scrape_url_task.s(url), save_html_task.s(platform=platform, name=unique_name), qpublic_parse_single_html_task.s(),
          import_to_db_task.s())()


#   -----------------------------------------------------------------------------------------
#   Одиночные задачи для использования внутри цепочек
#   -----------------------------------------------------------------------------------------

@app.task
def scrape_url_task(url: str) -> str:
    try:
        result = scrape_single_url(url)
        return result
    except Exception as e:
        error_string = f"Ошибка scrape_single_url:\nURL: {url}\n{e}\n\n"
        logging.error(error_string)
        print(error_string)
        return error_string


@app.task
def save_html_task(html: str, platform: str, name: str) -> str:
    try:
        save_html(html, platform, name)
        return html
    except Exception as e:
        file_path = f"/storage/{platform}/{name}.html"
        error_string = f"Ошибка save_html_task: {file_path}\n{e}\n\n"
        logging.error(error_string)
        print(error_string)
        return html


@app.task
def qpublic_parse_html_task(html: str) -> dict:
    try:
        data = qpublic_parse_single_html_task(html)
        return data
    except Exception as e:
        error_string = f"Ошибка qpublic_parse_html:\n{e}\n\n"
        logging.error(error_string)
        print(error_string)
        return {"error": error_string}


@app.task
def save_csv_task(data: dict, platform: str, name: str) -> dict:
    try:
        save_csv(data, platform, name)
        return data
    except Exception as e:
        error_string = f"Ошибка save_csv:\nCSV: /storage/{platform}/{name}.html\n{e}\n\n"
        logging.error(error_string)
        print(error_string)
        return data


@app.task
def import_to_db_task(data: dict) -> str:
    try:
        import_to_db(data)
        return "Данные импортированы в базу"
    except Exception as e:
        error_string = f"Ошибка import_to_db:\nДанные: {data}\n{e}\n\n"
        logging.error(error_string)
        print(error_string)
        return f"Ошибка импорта в базу: {error_string}"
