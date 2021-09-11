import sqlite3
from clint import textui

from exit_process import exit_process


class Videos_Database:
    def __init__(self, directory):
        """initialises database connection

        Args:
            directory (pathlib.Path): path object where database is to be stored
        """
        self.__directory = directory
        self.__conn = None
        self.__cur = None

        try:
            self.connect_to_db()
        except sqlite3.OperationalError as err:
            if "unable to open database file" in err.args:
                self.prompt_to_create_directory()

    def __del__(self):
        if self.__conn:
            self.__conn.close()

    def connect_to_db(self):
        self.__conn = sqlite3.connect(self.__directory / "gb_videos.db")
        self.__cur = self.__conn.cursor()

    def check_table_exists(self):
        """Checks if videos table is present in database

        Returns:
            boolean: True if videos exists, False if not
        """
        self.__cur.execute(
            (
                "SELECT name FROM sqlite_master "
                "WHERE type='table' "
                "AND name='videos';"
            )
        )
        return self.__cur.fetchone() != None

    def create_table(self):
        """creates videos table"""
        self.__cur.execute(
            (
                "CREATE TABLE IF NOT EXISTS videos( "
                "id int NOT NULL PRIMARY KEY, "
                "name text NOT NULL, "
                "publish_date text NOT NULL, "
                "url text NOT NULL "
                ");"
            )
        )

    def check_for_video(self, id):
        """checks database for a given video id

        Arguments:
            id {int} -- id for video to be queried

        Returns:
            boolean -- True if id already exists in database, False if not
        """
        # fmt: off
        self.__cur.execute(
          (
            "SELECT id FROM videos "
            f"WHERE id='{id}';"
          )
        )
        # fmt: on
        return self.__cur.fetchone() != None

    def insert_video(self, id, name, publish_date, url, show_title):
        """inserts video data into database

        Args:
            id (int): Video ID
            name (string): Name of video
            publish_date (string): Publish date of video
            url (string): url of video
        """
        # fmt: off
        self.__cur.execute(
            (
                "INSERT INTO videos(id, name, publish_date, url) "
                "VALUES(?,?,?,?)"
            ),
            (id, name, publish_date, url),
        )
        # fmt: on

        self.__conn.commit()

    def prompt_to_create_directory(self):
        user_input = textui.prompt.options(
            "Given Directory does not exist. Would you like to create it?",
            [
                {"selector": "y", "prompt": "Create Directory", "return": True},
                {"selector": "n", "prompt": "Cancel Process", "return": False},
            ],
        )

        if user_input:
            self.__directory.mkdir(parents=True)
            self.connect_to_db()
        else:
            exit_process()
