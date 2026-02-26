#!/bin/bash

cd /home/alx-got-it/taxlien
source venv/bin/activate

nohup ./dev_run_celery.sh > celery.log 2>&1 &
nohup ./dev_run_celery_beat.sh > celery_beat.log 2>&1 &
nohup ./dev_run_flower.sh > flower.log 2>&1 &