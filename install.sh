#!/bin/sh

# Install python executable
sudo mkdir -p /usr/local/share/sunset_timer
sudo cp ./requirements.txt /usr/local/share/sunset_timer/
sudo cp ./sunset_timer.py /usr/local/share/sunset_timer/
sudo cp ./LICENSE /usr/local/share/sunset_timer/

# Install system service
sudo cp ./sunset_timer.service /etc/systemd/system/
sudo chmod 640 /etc/systemd/system/sunset_timer.service
sudo systemctl enable sunset_timer 
sudo systemctl daemon-reload 
sudo systemctl start sunset_timer
