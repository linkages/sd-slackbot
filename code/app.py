from crypt import methods
import os
import requests
import json
import random
import urllib.parse
from datetime import datetime
import base64
import pprint

from flask import abort, Flask, config, jsonify, request, json, render_template, Response, make_response, g
import logging
from multiprocessing import Process
from celery import Celery

outdir="/out/"
logdir = os.environ['logdir']
domain= os.environ['domain']
#debug = os.environ['debug']
debug = True
#app.logger.info(f'Debug: {debug}\nToken: {postTokens}')

app = Flask(__name__)
app.config.from_object("config")

FORMAT = '[%(asctime)s]  %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT, filename=logdir + "slackbot.log")
app.logger.info("Starting up....")

# Set up celery client
client = Celery(app.name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])
# client.conf.update(app.config)

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
    is_token_valid = request.form['token'] in os.environ['token'].split(',')
    is_team_id_valid = request.form['team_id'] in os.environ['team'].split(',')

#    app.logger.debug(request.form)
    
    return is_token_valid and is_team_id_valid

@app.route('/aidream', methods=['POST'])
def aidream():
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

@app.route('/events', methods=['POST'])
def events():
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
                    app.logger.debug("Events: Got an event_callback of type: {type}".format(type=event_type))
                case _:
                    app.logger.debug("Events: Got some unknown event: {data}".format(data=data))
            
            return rDict
    else:
        app.logger.debug("Events: got something but I don't know what it was: {data}".format(data=request.get_data()))
        return ""

@app.route('/', methods=['GET'])
def slash():
    return "<html><a href=\"https://github.com/linkages/dadjokes\">Dad jokes repo</a></html>"

if __name__ == '__main__':
    app.run(debug=True)
