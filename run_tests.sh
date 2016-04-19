#!/bin/sh
export DJANGO_SETTINGS_MODULE="testproject.settings"
exec ./testproject/manage.py test -v3
