#!/bin/bash

# Install virtual environment
sudo pip3 install virtualenv
sudo apt-get install python3-venv

# Create a new virtual environment
python3 -m venv .venv
source .venv/bin/activate

pip3 install opencv-contrib-python