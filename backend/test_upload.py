import requests

url = "http://127.0.0.1:8000/upload-video"
files = {'video': ('test.mp4', b'dummy content', 'video/mp4')}
response = requests.post(url, files=files)
print(response.status_code, response.text)
