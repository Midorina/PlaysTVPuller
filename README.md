# PlaysTVPuller
Download your PlaysTV videos after shutdown!

This script will allow you to download almost all of your PlaysTV videos post shutdown.

## How does it work?
It uses Internet Archive to access the latest archived version of your Plays TV profile and attempts to download each one of your videos with highest quality possible. (I was able to download %97 of my videos)

## Requirements
1. [Python 3.7+](https://www.python.org/downloads/)
2. [git](https://git-scm.com/downloads)
3. [Selenium web driver for your desired browser downloaded and added to your PATH.](https://www.selenium.dev/documentation/en/webdriver/driver_requirements/#quick-reference)
4. Libraries located in the `requirements.txt` file. (They will be installed below.)

## Installation and Usage
1. Install the repo and change your directory to the script's location
```
git clone https://github.com/Midorina/PlaysTVPuller
cd PlaysTVPuller
```
2. Install the required libraries
```
python -m pip install -r requirements.txt
```
3. Run the script with your Plays.TV username
```
python playstvpuller.py YourPlaysTVUsername
```
That's it! The script will keep you informed in the process.

## Options
```
usage: playstvpuller.py [-h] [-p PATH] [-f] [--headless] username

Download most of your Plays.TV videos from the web archive.

positional arguments:
  username              your Plays.TV username

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  the directory where all videos will be placed in
  -f, --force           overwrite/re-download if the video is already downloaded
  --headless            use a headless browser (no gui)
```
