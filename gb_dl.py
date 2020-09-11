import pathlib
import sqlite3
import sys
import os

try:
    import requests
except ModuleNotFoundError:
    print("###  pip install requests  ###")
    raise

try:
    from clint.textui import progress, puts, indent, colored, prompt
except ModuleNotFoundError:
    print("### pip install clint ###")
    raise


class Giant_Bomb_Downloader:
    def __init__(self, api_key, directory="", filter_titles=[]):
        self.__api_key = api_key
        self.__directory = directory
        self.__filter_titles = filter_titles
        self.__conn = sqlite3.connect(f"{self.__directory}gb_videos.db")
        self.__cur = self.__conn.cursor()
        self.__videos = []
        self.__current_video = {}

    def __del__(self):
        self.__conn.close()

    @staticmethod
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

    def filter_shows(self, video):
        """checks if show is undesired type

      Arguments:
          show {dict} -- api response dict

      Returns:
          boolean -- True if video wanted, False if unwanted
      """

        return not (
            video["video_show"] and video["video_show"]["title"] in self.__filter_titles
        )

    def check_database(self, url):
        """checks database for a given video url

        Arguments:
            url {string} -- url for video to be queried

        Returns:
            boolean -- True if url already exists in database, False if not
        """
        self.__cur.execute(f"SELECT url FROM videos where url='{url}'")
        return self.__cur.fetchone() != None

    def insert_into_database(self, video):
        """inserts video data in to sqlite3 database

        Arguments:
            video {dict} -- dict containing data for video to be written
        """
        self.__cur.execute(
            "INSERT INTO videos(name, publish_date, url) VALUES(?,?,?)",
            (video["name"], video["publish_date"], video["url"]),
        )
        self.__conn.commit()

    # queries api for 100 most recent videos and initiates download process
    def query_api(self):

        puts("Retrieving Videos...")

        url = "https://www.giantbomb.com/api/videos/"
        params = {
            "api_key": self.__api_key,
            "format": "json",
        }
        response = requests.get(
            url, headers={"User-agent": "gb_dl"}, params=params
        )

        self.__videos = response.json()["results"]
        self.parse_api_response()

        with indent(2):
            puts(f"{len(self.__videos)} new videos")

        if self.__videos:
            self.download_videos()

        puts("All videos downloaded")

    # Turns self.__videos into usable form
    def parse_api_response(self):
        self.__videos = [
            {
                "name": Giant_Bomb_Downloader.correct_file_name(
                    video["name"], pathlib.Path(video["high_url"]).suffix
                ),
                "publish_date": video["publish_date"],
                "url": video["high_url"],
            }
            for video in self.__videos
            if self.filter_shows(video) and not self.check_database(video["high_url"])
        ]

        # Put vidoes in chronological order
        self.__videos.reverse()

    # Downloads all videos in self.__videos
    def download_videos(self):
        num_videos = len(self.__videos)

        for count, video in enumerate(self.__videos, start=1):
            self.__current_video = video

            puts(f"Downloading {count} of {num_videos}...")
            with indent(4, quote="  -"):
                puts(f"{video['name']} : {video['publish_date']}")

            r = requests.get(f"{video['url']}?api_key={self.__api_key}", stream=True)

            with open(f"{self.__directory}{video['name']}", "wb") as f:
                total_length = int(r.headers.get("content-length"))

                with indent(4):
                    for chunk in progress.bar(
                        r.iter_content(chunk_size=1024),
                        expected_size=(total_length / 1024) + 1,
                    ):
                        if chunk:
                            f.write(chunk)
                            f.flush()

            self.insert_into_database(video)

    def skip_current_video(self):
        # Add videos details to database so it will not be downloaded in the future
        self.insert_into_database(self.__current_video)
        # Delete partially downloaded file
        os.remove(f"{self.__directory}{self.__current_video['name']}")

    # Handles user interrupt process
    def prompt_for_skip(self):
        user_input = prompt.options(
            "Do you want to skip the current video?",
            [
                {"selector": "y", "prompt": "Skip Video", "return": True},
                {"selector": "n", "prompt": "Do Not Skip Video", "return": False},
            ],
        )

        if user_input:
            self.skip_current_video()

    # Iniitalise process
    def start(self):
        try:
            self.query_api()
        except KeyboardInterrupt:
            self.prompt_for_skip()
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)


if __name__ == "__main__":
    downloader = Giant_Bomb_Downloader(
        api_key="<API KEY>",
        directory="<directory>",
        filter_titles=[
            "Giant Bombcast",
            "The Giant Beastcast",
            "Premium Podcasts",
        ],
    )

    downloader.start()
