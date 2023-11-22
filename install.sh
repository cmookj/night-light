#!/bin/sh

# Install python executable
sudo python3 -m venv /usr/local/share/venv
source /usr/local/share/venv/bin/activate
sudo cp ./requirements.txt /usr/local/share/venv/bin/
sudo cp ./sunset_timer.py /usr/local/share/venv/bin/
sudo cp ./LICENSE /usr/local/share/venv/bin/
sudo /usr/local/share/venv/bin/python3 -m pip install -r requirements.txt

# Install system service
sudo cp ./sunset_timer.service /etc/systemd/system/
sudo chmod 640 /etc/systemd/system/sunset_timer.service
sudo systemctl enable sunset_timer
sudo systemctl daemon-reload
sudo systemctl start sunset_timer
