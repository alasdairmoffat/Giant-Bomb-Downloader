import datetime
import json
import requests
import urllib.request

directory = '<directory>'

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open(f'{directory}gb_most_recent', 'r') as f:
    lastPublishDate = datetime.datetime.strptime(f.read(), '%Y-%m-%d %H:%M:%S')

api_key = '<API KEY>'
url = f'https://www.giantbomb.com/api/videos/'
params = {
    'api_key': api_key,
    'format': 'json',
    'filter': f'publish_date:{lastPublishDate + datetime.timedelta(seconds=1)}|{now}'
}

response = requests.get(url,
                        headers={'User-agent': 'gb_dl'},
                        params=params)

# we extract just the list of videos, and reverse it so that we download in chronological order
videos = response.json()['results']
videos.reverse()

# data = json.loads(response)

'''
name is in videos[index]['name']
download is in videos[index]['high_url']
date is in videos[index]['publish_date']
Bombcast has videos[index]['video_show']['title'] == 'Giant Bombcast'
'''


if videos:
    for x in videos:
        if x['video_show'] is None or x['video_show']['title'] != 'Giant Bombcast':
            videoName = x['name'].replace(':', ' -')
            videoDate = x['publish_date']
            targetURL = f"{x['high_url']}?api_key={api_key}"
            print(f'Downloading {videoName} : {videoDate}...')

            # urllib.request.urlretrieve(
            #     targetURL, f'{directory}{videoName}.mp4')

            r = requests.get(targetURL)
            with open(f'{directory}{videoName}', 'wb') as f:
                f.write(r.content)

            print('...Download complete')
            with open(f'{directory}gb_most_recent', 'w') as f:
                f.write(videoDate)
