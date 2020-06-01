import requests
import sqlite3
import pathlib


def correct_file_name(name, extension):
    char_replacements = {
        ":": " -",
        "/": "-",
        '"': "'",
        "\\": "",
        "?": "",
        "%": "",
        "*": "",
        "|": "",
        "<": "",
        ">": "",
    }

    new_name = name.translate(str.maketrans(char_replacements))
    return f"{new_name}{extension}"


def get_json():
    api_key = "<API KEY>"
    url = "https://www.giantbomb.com/api/videos/"
    params = {
        "api_key": api_key,
        "format": "json",
        "filter": "publish_date:2020-04-01 16:31:00|2020-05-29 18:00:00",
    }
    response = requests.get(url, headers={"User-agent": "VideoSearch"}, params=params)

    response_json = response.json()

    final_json = [
        {
            "name": correct_file_name(
                video["name"], pathlib.Path(video["high_url"]).suffix
            ),
            "publish_date": video["publish_date"],
            "url": video["high_url"],
        }
        for video in response_json["results"]
    ]

    return final_json


conn = sqlite3.connect("gb_videos.db")

cur = conn.cursor()

cur.execute(
    "CREATE TABLE IF NOT EXISTS videos( name text NOT NULL, publish_date text NOT NULL, url text NOT NULL)"
)

for video in get_json():
    cur.execute(
        "INSERT INTO videos(name, publish_date, url) VALUES(?,?,?)",
        (video["name"], video["publish_date"], video["url"]),
    )
    conn.commit()

conn.close()
