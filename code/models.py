#!/usr/bin/env python3

import shutil
import requests
import base64
from datetime import datetime

url = 'https://user:xxxxxxxxxxxx@ai.benshoshan.com/sdapi/v1/sd-models'

r = requests.get(url)
if r.status_code == 200:
    data = r.json()
    for item in data:
      print(f"{item['model_name']}: {item['title']}")
else:
    print("Something went wrong: [{status}]".format(status=r.status_code))

del r
