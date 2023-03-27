import os
import json
import requests
from datetime import datetime
import base64

from celery import Celery
from celery.utils.log import get_task_logger

# Set up celery client
client = Celery(__name__, backend="redis://redis:6379/2", broker="redis://redis:6379/2")
# client.conf.update(app.config)

outdir="/out/"
workerConfig = "/config/worker.json"

domain= os.environ.get("domain")
auth_token = os.environ.get("auth_token")

token = os.environ.get("token")
team = os.environ.get("team")

logger = get_task_logger(__name__)
logger.info(f"Opening {workerConfig} file...")

with open(workerConfig) as file:
    config = json.load(file)

@client.task(name="fetch_and_reply")
def fetch_and_reply(query, channel, bot):
    logger.debug(f"Starting up image processing task for [{bot}]")
    logger.debug(f"Config file is:\n{config}\n")

    steps = config[bot]["steps"]
    scale = config[bot]["scale"]
    sampler = config[bot]["sampler"]
    width = config[bot]["width"]
    height = config[bot]["height"]
    checkpoint = config[bot]["checkpoint"]
    username = config[bot]["username"]
    password = config[bot]["password"]
    sdDomain = config[bot]["sdDomain"]
    negativePrompt = config[bot]["negativePrompt"]

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
        logger.info(f"Something went wrong creating the image: [{r.status_code}]")

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

    logger.info(f"Posting to channel: [{channel}]")
    logger.debug(f"Going to post this: {rDict}")
    chatUrl = 'https://slack.com/api/chat.postMessage'
    r = requests.post(chatUrl, headers=headers, json=rDict)
    if r.status_code == 200:
        logger.debug(f"Response: {r.json}")
    else:
        logger.info(f"Something went wrong: [{r.status_code}]")

    del r
