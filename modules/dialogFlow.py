import os

from dotenv import load_dotenv
from google.cloud import dialogflow_v2beta1 as dialogflow
from google.api_core.exceptions import InvalidArgument

load_dotenv()

def detectIntent(inp):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("PRIVATE-KEY-JSON")

    DIALOGFLOW_PROJECT_ID = 'asclepiusdiscord'
    DIALOGFLOW_LANGUAGE_CODE = 'en'
    SESSION_ID = 'me'

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(text=inp, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise

    detectedIntent = response.query_result.intent
    fullfillmentText = response.query_result.fulfillment_text
    sentimentScore = response.query_result.sentiment_analysis_result.query_text_sentiment.score

    return detectedIntent, fullfillmentText, sentimentScore