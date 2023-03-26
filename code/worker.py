import os
import requests
from datetime import datetime
import base64

from celery import Celery
from celery.utils.log import get_task_logger

# Set up celery client
client = Celery(__name__, backend="redis://redis:6379/2", broker="redis://redis:6379/2")
# client.conf.update(app.config)

outdir="/out/"
domain= os.environ.get("domain","ai.wiggels.dev")
auth_token = os.environ.get("auth_token","")

steps = os.environ.get("steps","25")
scale = os.environ.get("scale","8")
sampler = os.environ.get("sampler","")
width = os.environ.get("width","768")
height = os.environ.get("height","768")
checkpoint = os.environ.get("checkpoint","")
username = os.environ.get("username","")
password = os.environ.get("password","")
sdDomain = os.environ.get("sdDomain","")
negativePrompt = os.environ.get("negativePrompt","")
token = os.environ.get("token","")
team = os.environ.get("team","")

logger = get_task_logger(__name__)

@client.task(name="fetch_and_reply")
def fetch_and_reply(query, channel):
    logger.debug("Starting up image processing task")
    url = f'https://{username}:{password}@{sdDomain}/sdapi/v1/txt2img'

    data = {
        "enable_hr": "false",
        "denoising_strength": 0,
        "firstphase_width": 0,
        "firstphase_height": 0,
        "hr_scale": 2,
        "hr_upscaler": "string",
        "hr_second_pass_steps": 0,
        "hr_resize_x": 0,
        "hr_resize_y": 0,
        "prompt": str(query),
        "styles": [
        ],
        "seed": -1,
        "subseed": -1,
        "subseed_strength": 0,
        "seed_resize_from_h": -1,
        "seed_resize_from_w": -1,
        "batch_size": 1,
        "n_iter": 1,
        "steps": steps,
        "cfg_scale": scale,
        "width": width,
        "height": height,
        "restore_faces": "false",
        "tiling": "false",
        "negative_prompt": str(negativePrompt),
        "eta": 0,
        "s_churn": 0,
        "s_tmax": 0,
        "s_tmin": 0,
        "s_noise": 1,
        "override_settings": {
            "sd_model_checkpoint": str(checkpoint)
        },
        "override_settings_restore_afterwards": "false",
        "script_args": [],
        "sampler_name": str(sampler),
        "sampler_index": str(sampler)
    }

    image_date = datetime.now().strftime("%Y-%m-%dT%H%M%S.%f")
    image_name = data["prompt"].replace(" ","_")
    uri = image_date + ".png"
    filename = outdir + image_date + ".png"

    imageurl = "https://{domain}/images/{uri}".format(domain=domain, uri=uri)
    markdown = "<{imageurl}|{query}>".format(imageurl=imageurl, query=query)

    r = requests.post(url, stream=True, json=data)
    if r.status_code == 200:
        data = r.json()
        imageData = data['images'][0]
        image = base64.b64decode(imageData)
        out_file = open(filename, 'wb')
        out_file.write(image)
        out_file.close()
    else:
        logger.info("Something went wrong creating the image: [{status}]".format(status=r.status_code))

    del r
    logger.debug("Finished image processing task")
    logger.debug("Creating message to post to user")

    rDict = {
        "channel": str(channel),
        "blocks": [
            {
                "type": "image",
                "image_url": str(imageurl),
                "alt_text": str(query)
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": str(markdown)
                }
            }
        ]
    }

    headers = {
        'Content-type': 'application/json',
        'Authorization': 'Bearer '+ auth_token
    }

    logger.debug("Posting to channel: [{channel}]".format(channel=channel))
    logger.debug("Going to post this: {data}".format(data=rDict))
    chatUrl = 'https://slack.com/api/chat.postMessage'
    r = requests.post(chatUrl, headers=headers, json=rDict)
    if r.status_code == 200:
        logger.debug("Response: {message}".format(message=r.json()))
    else:
        logger.info("Something went wrong: [{status}]".format(status=r.status_code))

    del r
