from crypt import methods
import os
import requests
import json
import random
import urllib.parse
from datetime import datetime
import base64
import pprint

from fastapi import Body, FastAPI, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse

#from flask import abort, Flask, config, jsonify, request, json, render_template, Response, make_response, g
import logging
from multiprocessing import Process
from celery import Celery

outdir="/out/"
# logdir = os.environ['logdir']
domain= os.environ.get("domain","ai.wiggels.dev")
#debug = os.environ['debug']
debug = True
#app.logger.info(f'Debug: {debug}\nToken: {postTokens}')
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

# app = Flask(__name__)
# app.config.from_object("config")

app = FastAPI()

# FORMAT = '[%(asctime)s]  %(message)s'
# logging.basicConfig(level=logging.DEBUG, format=FORMAT, filename=logdir + "slackbot.log")
# app.logger.info("Starting up....")

# Set up celery client
client = Celery(__name__, backend="redis://redis:6379", broker="redis://redis:6379")
# client.conf.update(app.config)

@client.task
def fetch_and_reply(query, channel):
    app.logger.debug("Starting up image processing task")
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
        app.logger.info("Something went wrong creating the image: [{status}]".format(status=r.status_code))

    del r
    app.logger.debug("Finished image processing task")
    app.logger.debug("Creating message to post to user")

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

    app.logger.debug("Posting to channel: [{channel}]".format(channel=channel))
    app.logger.debug("Going to post this: {data}".format(data=rDict))
    chatUrl = 'https://slack.com/api/chat.postMessage'
    r = requests.post(chatUrl, headers=headers, json=rDict)
    if r.status_code == 200:
        app.logger.debug("Response: {message}".format(message=r.json()))
    else:
        app.logger.info("Something went wrong: [{status}]".format(status=r.status_code))

    del r

@client.task
def fetch_image_task(url, data, filename):
    app.logger.debug("Starting up image processing task")
    r = requests.post(url, stream=True, json=data)
    if r.status_code == 200:
        output = r.json()['output'][0]
        base64string = output.replace("data:image/png;base64,","")
        image = base64.b64decode(base64string)
        out_file = open(filename, 'wb')
        out_file.write(image)
        out_file.close()
    else:
        app.logger.info("Something went wrong: [{status}]".format(status=r.status_code))

    del r
    app.logger.debug("Finished image processing task")

def fetch_image(url, data, filename):
#    app.logger.debug("Starting up image processing")
    r = requests.post(url, stream=True, json=data)
    if r.status_code == 200:
        output = r.json()['output'][0]
        base64string = output.replace("data:image/png;base64,","")
        image = base64.b64decode(base64string)
    else:
        app.logger.info("Something went wrong: [{status}]".format(status=r.status_code))
        image = None

    del r
#    app.logger.debug("Finished image processing")
    return image
    
def is_request_valid(request):
    is_token_valid = request.form['token'] in token.split(',')
    is_team_id_valid = request.form['team_id'] in team.split(',')

#    app.logger.debug(request.form)
    
    return is_token_valid and is_team_id_valid

@app.post('/aidream')
async def aidream():
    if not is_request_valid(request):
        abort(400)

    if request.form['text'] is not None:
        query=request.form['text']
    else:
        query="I dream of androids"

    data = {
        "input": {
            "prompt": str(query),
            "width": "512",
            "height": "512",
            "num_outputs": "1"
        }
    }

    image_date = datetime.now().strftime("%Y-%m-%dT%H%M%S.%f")
    image_name = data["input"]["prompt"].replace(" ","_")
    uri = image_date + "+" + image_name + ".png"
    filename = outdir + image_date + "+" + image_name + ".png"
    
    imageurl = "https://{domain}/images/{uri}".format(domain=domain, uri=uri)
    markdown = "<{imageurl}|{query}>".format(imageurl=imageurl, query=query)
    
    rDict = {
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
        ],
        "response_type": "in_channel"
    }

    url = 'http://diffusion:5000/predictions'

    app.logger.debug("Scheduling the image creation task")
    fetch_image_task.apply_async(args=[url, data, filename])
#    app.logger.debug("Calling Image processing function returned")
#    image = fetch_image(url, data, filename)
#    app.logger.debug("Image processing function returned")

    # if image is not None:
    #     out_file = open(filename, 'wb')
    #     out_file.write(image)
    #     out_file.close()
    
    # app.logger.debug("DEBUG: {rDict}".format(rDict=rDict))

    return rDict

@app.post('/events/r34')
async def events(payload = Body(...)):
    rDict = {}
    if request.is_json:
        data = request.get_json()
        if data['type'] is not None:
            match data['type']:
                case "url_verification":
                    rDict = {
                        'challenge': data['challenge']
                    }
                case "event_callback":
                    event = data['event']
                    event_type = event['type']
                    original_text = event['text']
                    channel = event['channel']
                    query = original_text.replace("<@U044UD23SP2>", "").strip()
                    app.logger.debug("Events: Got an event_callback of type: {type}".format(type=event_type))
                    app.logger.debug("Events: User said the following: [{query}]".format(query=query))
                    fetch_and_reply.apply_async(args=[query, channel])
                case _:
                    app.logger.debug("Events: Got some unknown event: {data}".format(data=data))
            
            return rDict
    else:
        app.logger.debug("Events: Got a non-json request: {data}".format(data=request.get_data()))
        return ""

def generate_html_response():
    html_content = """
    <html>
        <head>
            <title>Slackbot</title>
        </head>
        <body>
            <p><a href=\"https://github.com/linkages/sd-slackbot\">SD Slackbot</a>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get('/events/r34', response_class=HTMLResponse)
async def slash():
    return generate_html_response()

if __name__ == '__main__':
    app.run(debug=True)
