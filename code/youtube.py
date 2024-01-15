import requests

# You need google accouont, get from our gmail


API_KEY = "YOUR_API_KEY"
VIDEO_ID = "VIDEO_ID"

url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={VIDEO_ID}&key={API_KEY}"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    video_title = data["items"][0]["snippet"]["title"]
    video_description = data["items"][0]["snippet"]["description"]
    print(f"Video title: {video_title}")
    print(f"Video description: {video_description}")
else:
    print("Error:", response.status_code)