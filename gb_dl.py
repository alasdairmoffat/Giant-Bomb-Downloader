import datetime
import pathlib
import unicodedata

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



def show_filter(show):
    unwanted_shows = [
        "Giant Bombcast",
        "The Giant Beastcast",
    ]
    if show["video_show"] and show["video_show"]["title"] in unwanted_shows:
        return False

    return True


directory = "<directory>"

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(f"{directory}gb_most_recent", "r", encoding="utf-16") as f:
    last_publish_date = datetime.datetime.strptime(
        f.read().replace("\n", ""), "%Y-%m-%d %H:%M:%S"
    )

api_key = "<API KEY>"
url = "https://www.giantbomb.com/api/videos/"
params = {
    "api_key": api_key,
    "format": "json",
    "filter": f"publish_date:{last_publish_date + datetime.timedelta(seconds=1)}|{now}",
    "sort": "publish_date:asc",
}

puts("Retrieving Videos...")
response = requests.get(url, headers={"User-agent": "gb_dl"}, params=params)

json = response.json()

with indent(2):
    puts(f"{json['number_of_total_results']} videos returned")

# extract the list of videos, and filter out unwanted shows
videos = list(filter(show_filter, json["results"]))

num_videos = len(videos)

if videos:
    for count, x in enumerate(videos, start=1):
        extension = pathlib.Path(x["high_url"]).suffix
        file_name = correct_file_name(x["name"], extension)
        video_date = x["publish_date"]
        target_URL = f"{x['high_url']}?api_key={api_key}"

        puts(f"Downloading {count} of {num_videos}...")
        with indent(4, quote="  -"):
            puts(f"{file_name} : {video_date}")

        r = requests.get(target_URL, stream=True)
        path = f"{directory}{file_name}"
        with open(path, "wb") as f:
            total_length = int(r.headers.get("content-length"))

            with indent(4):
                for chunk in progress.bar(
                    r.iter_content(chunk_size=1024),
                    expected_size=(total_length / 1024) + 1,
                ):
                    if chunk:
                        f.write(chunk)
                        f.flush()

        with open(f"{directory}gb_most_recent", "w", encoding="utf-16") as f:
            f.write(video_date)


print("All videos downloaded")
