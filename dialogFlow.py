import os
from google.cloud import dialogflow_v2beta1 as dialogflow
from google.api_core.exceptions import InvalidArgument


def detectIntent(input):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("PRIVATE-KEY-JSON")

    DIALOGFLOW_PROJECT_ID = 'newagent-fcbi'
    DIALOGFLOW_LANGUAGE_CODE = 'en'
    SESSION_ID = 'me'

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(text=input, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise

    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent)
    print("Fulfillment text:", response.query_result.fulfillment_text)
    print("Sentiment score:",  response.query_result.sentiment_analysis_result.query_text_sentiment.score)

