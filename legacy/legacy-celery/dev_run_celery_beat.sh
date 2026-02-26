#!/bin/bash

# Start the Celery-beat worker
celery -A tasks beat --loglevel=debug

# Start the Celery-beat in the background
#nohup celery -A tasks beat --loglevel=info &