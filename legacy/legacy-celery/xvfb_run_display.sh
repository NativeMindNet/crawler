#!/bin/bash

# Activate Headless Display (Xvfb)

#Xvfb -ac :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
#export DISPLAY=:99
#exec "$@"

# Запуск виртуального дисплея
Xvfb -ac :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
export DISPLAY=:99

# Запуск VNC сервера
x11vnc -display :99 -forever -noxdamage -passwd qwertyuiop1234 &

# Подключение через SSH с пробросом порта
echo "VNC сервер запущен на порту 5900"
# Запуск приложения
exec "$@"