#!/usr/bin/env python3

import shutil
import requests
import base64
from datetime import datetime

outdir = "./out/"

data = {
    "input": {
        "prompt": "something with a single ' in it",
        "width": "512",
        "height": "512",
        "num_outputs": "1"
    }
}

url = 'http://localhost:5000/predictions'
r = requests.post(url, stream=True, json=data)
if r.status_code == 200:
    output = r.json()['output'][0]
    base64string = output.replace("data:image/png;base64,","")
    image = base64.b64decode(base64string)
    image_date = datetime.now().strftime("%Y-%m-%dT%H%M")
    image_name = data["input"]["prompt"].replace(" ","_")
    filename = outdir + image_date + "+" + image_name
    out_file = open(filename, 'wb')
    out_file.write(image)
    out_file.close()
else:
    print("Something went wrong: [{status}]".format(status=r.status_code))

del r
