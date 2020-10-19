# Giant Bomb Video Downloader

> Python CLI app to download videos from [Giant Bomb](giantbomb.com)

[![License](https://img.shields.io/:license-mit-blue.svg?style=flat-square)](https://badges.mit-license.org)

## Table of Contents

- [General Info](#general-info)
- [Usage](#usage)
- [Technologies](#technologies)
- [Setup](#setup)
- [License](#license)

## General Info

Requires Giant Bomb API key obtainable [here](https://www.giantbomb.com/api/).

Will poll the Giant Bomb API for 100 most recent videos and download any not previously downloaded.

Supports resuming of partially downloaded videos.

User can cancel process with `Ctrl+C` which will give the option to skip the current video. Next time the app is run downloading will begin from the next video.

### Usage

Help can be obtained by running the application with the `--help` option. The following commands will be shown:

```bash
usage: gb_dl.py [-h] [-a APIKEY] [-d DIRECTORY] [-f FILTERTITLES]
                [-q VIDEOQUALITY] [-s DAYSBACKTOSTART]

Download Videos from Giant Bomb.

optional arguments:
  -h, --help            show this help message and exit
  -a APIKEY, --apikey APIKEY
                        Giant Bomb API key. Available from
                        https://www.giantbomb.com/api/
  -d DIRECTORY, --directory DIRECTORY
                        Directory to store downloaded videos. (Default: ./)
  -f FILTERTITLES, --filtertitles FILTERTITLES
                        List of show titles to skip seperated by commas. (Wrap
                        in '' if spaces required)
  -q VIDEOQUALITY, --videoquality VIDEOQUALITY
                        Video quality ('low', 'high' or 'hd'). (Default: hd)
  -s DAYSBACKTOSTART, --daysbacktostart DAYSBACKTOSTART
                        Number of days back to start downloading videos from
                        if running for the first time. (Default: 7)
```

Options can also be configured in a config file stored as `~/.gb_dl/gb_dl.config`. An example of this file with all available options:

```config
[gb_dl]
api_key = <API_KEY>
directory = <directory>
filter_titles = Giant Bombcast
                The Giant Beastcast
                Premium Podcasts
video_quality = high
days_back_to_start = 4
```

## Technologies

- Python 3.7.4
- SQLite
- requests

## Setup

### Clone

Clone from repository

```bash
git clone https://github.com/alasdairmoffat/Giant-Bomb-Downloader.git
```

## License

> **[MIT license](https://opensource.org/licenses/mit-license.php)**
