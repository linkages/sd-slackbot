import os
import logging

from fastapi import Body, FastAPI, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse

from worker import fetch_and_reply

app = FastAPI()

# logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

token = os.environ.get("token","")
team = os.environ.get("team","")
botname = os.environ.get("botname", "<@U04VCKFJK17> ")

def is_request_valid(request):
    is_token_valid = request.form['token'] in token.split(',')
    is_team_id_valid = request.form['team_id'] in team.split(',')

#    logger.debug(request.form)
    
    return is_token_valid and is_team_id_valid

@app.post('/events/{bot}')
async def events(bot: str, payload = Body(...)):
    logger.debug(f'Got called: {payload}')
    logger.info(f'[{bot}] bot was called')
    rDict = {}
    if payload['type'] is not None:
        match payload['type']:
            case "url_verification":
                logger.info("Doing a challenge verification")
                rDict = {
                    'challenge': payload['challenge']
                }
            case "event_callback":
                event = payload['event']
                event_type = event['type']
                original_text = event['text']
                channel = event['channel']
                query = original_text.replace(botname, "").strip()
                logger.debug(f'Got an event_callback of type: {event_type}')
                logger.info(f'User query is: [{query}]')
                fetch_and_reply.apply_async(args=[query, channel])
            case _:
                logger.info(f"Got some unknown event type: { payload['type'] }")

    return JSONResponse(rDict)

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

@app.get('/events/{bot}', response_class=HTMLResponse)
async def slash(bot: str):
    return generate_html_response()
