#!/bin/bash

# Start the Celery worker
celery -A tasks worker --loglevel=debug

# Start the Celery worker in the background
#nohup celery -A tasks worker --loglevel=info &