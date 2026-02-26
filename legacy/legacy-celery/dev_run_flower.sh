#!/bin/bash

# Start the Celery worker
celery -A tasks --broker=redis://localhost:6379/0 flower --port=5555 --loglevel=debug

# Start the Celery worker in the background
#nohup celery -A tasks --broker=redis://localhost:6379/0 flower --port=5555 --loglevel=info &