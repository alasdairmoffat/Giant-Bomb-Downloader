import datetime
import pathlib
import unicodedata

try:
    import requests
except ModuleNotFoundError:
    print("###  pip install requests  ###")
    raise

try:
    from clint.textui import progress
except ModuleNotFoundError:
    print('### pip install clint ###')
    raise

directory = '<directory>'

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open(f'{directory}gb_most_recent', 'r') as f:
    lastPublishDate = datetime.datetime.strptime(f.read(), '%Y-%m-%d %H:%M:%S')

api_key = '<API KEY>'
url = 'https://www.giantbomb.com/api/videos/'
params = {
    'api_key': api_key,
    'format': 'json',
    'filter': f'publish_date:{lastPublishDate + datetime.timedelta(seconds=1)}|{now}'
}

print('Retrieving Videos...')
response = requests.get(url,
                        headers={'User-agent': 'gb_dl'},
                        params=params)

# we extract just the list of videos, and reverse it so that we download in chronological order
videos = response.json()['results']
videos.reverse()

count = 1
numVideos = len(videos)


def correctFileName(name, extension):
    newName = name.replace(':', ' -')
    newName = newName.replace('/', '-')
    newName = newName.replace('"', '\'')
    charsToRemove = ['\\', '?', '%', '*', '|', '<', '>']
    for char in charsToRemove:
        newName = newName.replace(char, '')
    return f'{newName}{extension}'


if videos:
    for x in videos:
        if x['video_show'] is None or x['video_show']['title'] != 'Giant Bombcast':
            extension = pathlib.Path(x['high_url']).suffix
            fileName = correctFileName(x['name'], extension)
            videoDate = x['publish_date']
            targetURL = f"{x['high_url']}?api_key={api_key}"
            print(
                f'Downloading {count} of {numVideos} - {fileName} : {videoDate}...')

            r = requests.get(targetURL, stream=True)
            path = f'{directory}{fileName}'
            with open(path, 'wb') as f:
                total_length = int(r.headers.get('content-length'))
                for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1):
                    if chunk:
                        f.write(chunk)
                        f.flush()

            with open(f'{directory}gb_most_recent', 'w') as f:
                f.write(videoDate)

        count += 1

print('All videos downloaded')
