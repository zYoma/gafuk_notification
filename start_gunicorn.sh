#!/bin/bash
exec gunicorn main:create_app --bind 0.0.0.0:8000 --worker-class aiohttp.GunicornWebWorker
