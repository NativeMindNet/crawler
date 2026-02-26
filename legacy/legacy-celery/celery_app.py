from celery import Celery

app = Celery('app', broker='redis://localhost:6379/0')
