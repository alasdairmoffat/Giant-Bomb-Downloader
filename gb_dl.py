import json
import pathlib
import sqlite3

try:
    import requests
except ModuleNotFoundError:
    print("###  pip install requests  ###")
    raise

try:
    from clint.textui import progress, puts, indent
except ModuleNotFoundError:
    print("### pip install clint ###")
    raise


def correct_file_name(name, extension):
    """Removes and substitutes characters that are invalid for filenames

    Arguments:
        name {string} -- name of video to be corrected
        extension {string} -- filename extension

    Returns:
        string -- corrected filename
    """
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


def check_database(url, conn):
    """checks database for a given video url

    Arguments:
        url {string} -- url for video to be queried
        conn {sqlite3 connection} -- connection to sqlite3 database

    Returns:
        boolean -- True if url already exists in database, False if not
    """
    cur = conn.cursor()
    cur.execute(f"SELECT url FROM videos where url='{url}'")
    return cur.fetchone() != None


def insert_into_database(video, conn):
    """inserts video data in to sqlite3 database

    Arguments:
        video {dict} -- dict containing data for video to be written
        conn {sqlite3 connection} -- connection to sqlite3 database
    """
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO videos(name, publish_date, url) VALUES(?,?,?)",
        (video["name"], video["publish_date"], video["url"]),
    )
    conn.commit()


def show_filter(show):
    """checks if show is undesired type

    Arguments:
        show {dict} -- api response dict

    Returns:
        boolean -- True if video wanted, False if unwanted
    """

    unwanted_shows = [
        "Giant Bombcast",
        "The Giant Beastcast",
    ]
    return not (show["video_show"] and show["video_show"]["title"] in unwanted_shows)


def query_api(api_key):
    """queries giantbomb api for 100 most recent videos

    Returns:
        json -- response json
    """

    url = "https://www.giantbomb.com/api/videos/"
    params = {
        "api_key": api_key,
        "format": "json",
    }
    response = requests.get(url, headers={"User-agent": "VideoSearch"}, params=params)

    return response.json()


def download_videos(videos, api_key, directory, conn):
    """downloads videos

    Arguments:
        videos {list} -- list of videos to be downloaded
        api_key {string} -- giantbomb api key
        directory {string} -- target directory to be downloaded to
        conn {sqlite3 connection} -- connection to sqlite3 database
    """
    num_videos = len(videos)

    for count, video in enumerate(videos, start=1):
        puts(f"Downloading {count} of {num_videos}...")
        with indent(4, quote="  -"):
            puts(f"{video['name']} : {video['publish_date']}")
            puts(f"{video['url']}")

        r = requests.get(f"{video['url']}?api_key={api_key}", stream=True)

        with open(f"{directory}{video['name']}", "wb") as f:
            total_length = int(r.headers.get("content-length"))

            with indent(4):
                for chunk in progress.bar(
                    r.iter_content(chunk_size=1024),
                    expected_size=(total_length / 1024) + 1,
                ):
                    if chunk:
                        f.write(chunk)
                        f.flush()

        insert_into_database(video, conn)


def main():
    directory = "<directory>"
    api_key = "<API KEY>"
    conn = sqlite3.connect(f"{directory}gb_videos.db")

    puts("Retrieving Videos...")
    response_json = query_api(api_key)

    videos_to_download = [
        {
            "name": correct_file_name(
                video["name"], pathlib.Path(video["high_url"]).suffix
            ),
            "publish_date": video["publish_date"],
            "url": video["high_url"],
        }
        for video in response_json["results"]
        if show_filter(video) and not check_database(video["high_url"], conn)
    ]

    # Download in chronological order
    videos_to_download.reverse()

    with indent(2):
        puts(f"{len(videos_to_download)} new videos")

    if videos_to_download:
        download_videos(videos_to_download, api_key, directory, conn)

    conn.close()
    puts("All videos downloaded")


if __name__ == "__main__":
    main()
