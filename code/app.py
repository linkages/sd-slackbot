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

def is_request_valid(request):
    is_token_valid = request.form['token'] in token.split(',')
    is_team_id_valid = request.form['team_id'] in team.split(',')

#    logger.debug(request.form)
    
    return is_token_valid and is_team_id_valid

@app.post('/events/r34')
async def events(payload = Body(...)):
    rDict = {}
    if payload['type'] is not None:
        match payload['type']:
            case "url_verification":
                rDict = {
                    'challenge': payload['challenge']
                }
            case "event_callback":
                event = payload['event']
                event_type = event['type']
                original_text = event['text']
                channel = event['channel']
                query = original_text.replace("<@U044UD23SP2>", "").strip()
                logger.debug("Events: Got an event_callback of type: {type}".format(type=event_type))
                logger.debug("Events: User said the following: [{query}]".format(query=query))
                fetch_and_reply.apply_async(args=[query, channel])
            case _:
                logger.debug("Events: Got some unknown event: {data}".format(data=data))

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

@app.get('/events/r34', response_class=HTMLResponse)
async def slash():
    return generate_html_response()

if __name__ == '__main__':
    app.run(debug=True)
