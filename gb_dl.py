import pathlib
import urllib
import configparser
import argparse
import datetime
import requests
from clint import textui

from videos_database import Videos_Database
from exit_process import exit_process


class Giant_Bomb_Downloader:
    def __init__(
        self,
        api_key,
        directory=pathlib.Path.cwd(),
        filter_titles=[],
        video_quality="hd",
        days_back_to_start=7,
    ):
        """Queries Giant Bomb API for videos and downloads any not stored in local database of previously downloaded files.

        Args:
            api_key (string): Giant Bomb API key
            directory (pathlib.Path, optional): Directory to download videos to. Defaults to pathlib.Path.cwd().
            filter_titles (list, optional): List of Giant Bomb show titles to skip. Defaults to [].
            days_back_to_start (int, optional): Days back to initialise database from if not already created. Defaults to 7.
        """
        self.__api_key = api_key
        self.__directory = directory
        self.__filter_titles = filter_titles
        self.__video_quality = video_quality
        self.__days_back_to_start = days_back_to_start
        self.__videos = []
        self.__current_video = {}
        self.__database = Videos_Database(directory)

        if not self.__database.check_table_exists():
            textui.puts("Creating New Database...")
            self.__database.create_table()
            self.initialise_database()

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

    def query_api(self, query_date=None):
        """queries api for 100 most recent videos up to optional query_date"""
        url = "https://www.giantbomb.com/api/videos/"
        params = {
            "api_key": self.__api_key,
            "format": "json",
        }

        if query_date:
            formatted_date = query_date.strftime("%Y-%m-%d %H:%M:%S")
            params["filter"] = f"publish_date:1970-01-01 00:00:00|{formatted_date}"

        response = requests.get(url, headers={"User-agent": "gb_dl"}, params=params)

        if response.status_code != 200:
            textui.puts(response.json()["error"])
            exit_process()

        self.__videos = response.json()["results"]

    @staticmethod
    def find_valid_url(video):
        """Finds a valid video url, not caring what video quality is

        Args:
            video (dict): video returned from api
        """
        return video["low_url"] or video["high_url"] or video["hd_url"]

    def get_download_url(self, video):
        """returns url for requested quality even if not surface in api response

        Args:
            video (dict): video returned from api

        Returns:
            string: url for video at requested quality
        """
        if video[f"{self.__video_quality}_url"]:
            return video[f"{self.__video_quality}_url"]

        bitrates = {"low": "1800", "high": "3200", "hd": "4000"}

        valid_url = urllib.parse.urlparse(Giant_Bomb_Downloader.find_valid_url(video))

        if valid_url.path:
            new_url = valid_url._replace(
                path=valid_url.path[:-8]
                + bitrates[self.__video_quality]
                + valid_url.path[-4:]
            )

            return new_url.geturl()
        else:
            return None

    def parse_api_response(self, filter=True):
        """Turns self.__videos into usable form

        Args:
            filter (bool, optional): Whether to apply filter to videos. Defaults to True.
        """
        filtered_videos = [
            video
            for video in self.__videos
            if not filter
            or self.filter_shows(video)
            and not self.__database.check_for_video(video["id"])
        ]

        self.__videos = []
        for video in filtered_videos:
            download_url = self.get_download_url(video)

            if not download_url:
                textui.puts("Skipping video with no valid URL:")
                with textui.indent(4, quote="  -"):
                    textui.puts(f"{video['name']}")

            else:
                self.__videos.append(
                    {
                        "id": video["id"],
                        "name": Giant_Bomb_Downloader.correct_file_name(
                            video["name"], pathlib.Path(download_url).suffix
                        ),
                        "publish_date": video["publish_date"],
                        "url": download_url,
                        "show_title": video["video_show"]["title"] if video['video_show'] else '',
                    }
                )

        # Put vidoes in chronological order
        self.__videos.reverse()

    def initialise_database(self):

        query_date = datetime.datetime.now() - datetime.timedelta(
            self.__days_back_to_start
        )

        self.query_api(query_date)
        self.parse_api_response(filter=False)
        for video in self.__videos:
            self.__database.insert_video(**video)

        # re-initialise self.__videos ready to begin download process
        self.__videos = []
        with textui.indent(2):
            textui.puts("Database Initialised")

    def download_videos(self):
        """Downloads all videos in self.__videos"""
        num_videos = len(self.__videos)

        for count, video in enumerate(self.__videos, start=1):
            self.__current_video = video
            file = self.__directory / video["name"]

            # Skip download if file already exists
            if file.exists():
                textui.puts(f"Already downloaded {count} of {num_videos}.")
                with textui.indent(4, quote=" -"):
                    textui.puts(f"{video['name']} : {video['publish_date']}")

                self.__database.insert_video(**video)
                continue

            temp_file = file.parent / (f"{file.name}_{self.__video_quality}.part")

            already_downloaded = temp_file.stat().st_size if temp_file.exists() else 0
            file_mode = "ab" if already_downloaded else "wb"

            textui.puts(f"Downloading {count} of {num_videos}...")
            with textui.indent(4, quote="  -"):
                textui.puts(
                    f"{video['name']} : {video['publish_date']} ({video['show_title']})"
                )

            params = {"api_key": self.__api_key}
            headers = {"Range": f"bytes={already_downloaded}-"}

            r = requests.get(
                video["url"], params=params, headers=headers, stream=True, timeout=5
            )
            r_length = int(r.headers.get("Content-length"))
            total_length = r_length + already_downloaded
            # set chunk_size to 1MB
            chunk_size = 1024 * 1024
            with open(temp_file, file_mode) as f:
                for chunk in textui.progress.bar(
                    r.iter_content(chunk_size=chunk_size),
                    expected_size=(r_length / chunk_size) + 1,
                ):
                    if chunk:
                        f.write(chunk)
                        f.flush()

            # Rename file and add to database if fully downloaded
            if total_length == temp_file.stat().st_size:
                temp_file.rename(file)
                self.__database.insert_video(**video)

    def skip_current_video(self):
        """Add videos details to database so it will not be downloaded in the future"""
        self.__database.insert_video(**self.__current_video)
        # Delete partially downloaded file
        (
            self.__directory
            / (f"{self.__current_video['name']}_{self.__video_quality}.part")
        ).unlink()

    def prompt_for_skip(self):
        """Handles user interrupt process"""
        user_input = textui.prompt.options(
            "Do you want to skip the current video?",
            [
                {"selector": "y", "prompt": "Skip Video", "return": True},
                {"selector": "n", "prompt": "Do Not Skip Video", "return": False},
            ],
        )

        if user_input:
            self.skip_current_video()

    def start(self):
        """Iniitalise process"""
        try:
            textui.puts("Retrieving Videos...")
            self.query_api()
            self.parse_api_response()

            with textui.indent(2):
                textui.puts(f"{len(self.__videos)} new videos")

            if self.__videos:
                self.download_videos()

            textui.puts("All videos downloaded")

        except KeyboardInterrupt:
            self.prompt_for_skip()
            exit_process()


class Options:
    def __init__(self):
        self.__api_key = None
        self.__video_quality = None
        self.__directory = None
        self.__filter_titles = []
        self.__days_back_to_start = None

        self.read_config_file()
        self.create_cli_args()

    @staticmethod
    def validate_video_quality(quality):
        return quality in ["low", "high", "hd"]

    def read_config_file(self):
        """Reads options from config file if present"""
        config = configparser.ConfigParser()
        config.read(pathlib.Path.home() / ".gb_dl/gb_dl.config")

        if "gb_dl" not in config:
            return

        gb_dl = config["gb_dl"]

        if "api_key" in gb_dl:
            self.__api_key = gb_dl["api_key"]
        if "directory" in gb_dl:
            self.__directory = pathlib.Path(gb_dl["directory"])
        if "filter_titles" in gb_dl:
            self.__filter_titles = gb_dl["filter_titles"].split("\n")
        if "video_quality" in gb_dl and Options.validate_video_quality(
            gb_dl["video_quality"]
        ):
            self.__video_quality = gb_dl["video_quality"]
        if "days_back_to_start" in gb_dl:
            self.__days_back_to_start = gb_dl["days_back_to_start"]

    def create_cli_args(self):
        """Handles cli argument parsing"""

        def check_quality(value):
            if not Options.validate_video_quality(value):
                raise argparse.ArgumentTypeError(
                    "videoquality must be 'low', 'high' or 'hd'"
                )
            return value

        parser = argparse.ArgumentParser(description="Download Videos from Giant Bomb.")
        parser.add_argument(
            "-a",
            "--apikey",
            help="Giant Bomb API key. Available from https://www.giantbomb.com/api/",
            required=False,
        )
        parser.add_argument(
            "-d",
            "--directory",
            help="Directory to store downloaded videos. (Default: ./)",
            required=False,
        )
        parser.add_argument(
            "-f",
            "--filtertitles",
            help="List of show titles to skip seperated by commas. (Wrap in '' if spaces required)",
            required=False,
        )
        parser.add_argument(
            "-q",
            "--videoquality",
            help="Video quality ('low', 'high' or 'hd'). (Default: 'hd')",
            required=False,
            type=check_quality,
        )
        parser.add_argument(
            "-s",
            "--daysbacktostart",
            type=int,
            help="Number of days back to start downloading videos from if running for the first time. (Default: 7)",
            required=False,
        )

        args = parser.parse_args()

        if args.apikey:
            self.__api_key = args.apikey
        if args.directory:
            self.__directory = pathlib.Path(args.directory).expanduser()
        if args.filtertitles:
            self.__filter_titles = [
                title.strip() for title in args.filtertitles.split(",")
            ]
        if args.videoquality:
            self.__video_quality = args.videoquality
        if args.daysbacktostart:
            self.__days_back_to_start = args.daysbacktostart

    def get_args(self):
        """returns all options where given from either config file or cli args

        Returns:
            dict: contains all options given in either config file or cli args
        """
        args = {
            "api_key": self.__api_key,
            "directory": self.__directory,
            "filter_titles": self.__filter_titles,
            "video_quality": self.__video_quality,
            "days_back_to_start": self.__days_back_to_start,
        }

        return {key: value for key, value in args.items() if value}


if __name__ == "__main__":
    options = Options()
    args = options.get_args()

    if not "api_key" in args:
        textui.puts("API key required")

    else:
        downloader = Giant_Bomb_Downloader(**args)

        downloader.start()
