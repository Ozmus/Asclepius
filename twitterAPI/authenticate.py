import configparser
import sys
import requests
from requests_oauthlib import OAuth1Session
import tweepy

config = configparser.ConfigParser()
config.read('config.ini')

CONSUMER_KEY = config['twitter']['api_key']
CONSUMER_SECRET = config['twitter']['api_key_secret']

def request_token():
    oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET, callback_uri='oob')
    url = "https://api.twitter.com/oauth/request_token"

    try:
        response = oauth.fetch_request_token(url)
        resource_owner_oauth_token = response.get('oauth_token')
        resource_owner_oauth_token_secret = response.get('oauth_token_secret')
    except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(120)
    
    return resource_owner_oauth_token, resource_owner_oauth_token_secret

# Use the OAuth Request Token received in the previous step to redirect the user to authorize your developer App for access.
def get_user_authorization(resource_owner_oauth_token):

    authorization_url = f"https://api.twitter.com/oauth/authorize?oauth_token={resource_owner_oauth_token}"
    authorization_pin = input(f" \n Send the following URL to the user you want to generate access tokens for. \n → {authorization_url} \n This URL will allow the user to authorize your application and generate a PIN. \n Paste PIN here: ")

    return(authorization_pin)

# Exchange the OAuth Request Token you obtained previously for the user’s Access Tokens.
def get_user_access_tokens(resource_owner_oauth_token, resource_owner_oauth_token_secret, authorization_pin):

    oauth = OAuth1Session(CONSUMER_KEY, 
                            client_secret=CONSUMER_SECRET, 
                            resource_owner_key=resource_owner_oauth_token, 
                            resource_owner_secret=resource_owner_oauth_token_secret, 
                            verifier=authorization_pin)
    
    url = "https://api.twitter.com/oauth/access_token"

    try: 
        response = oauth.fetch_access_token(url)
        access_token = response['oauth_token']
        access_token_secret = response['oauth_token_secret']
        user_id = response['user_id']
        screen_name = response['screen_name']
    except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(120)

    return(access_token, access_token_secret, user_id, screen_name)

if __name__ == '__main__':
    resource_owner_oauth_token, resource_owner_oauth_token_secret = request_token()
    authorization_pin = get_user_authorization(resource_owner_oauth_token)
    access_token, access_token_secret, user_id, screen_name = get_user_access_tokens(resource_owner_oauth_token, resource_owner_oauth_token_secret, authorization_pin)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    username = screen_name
    new_tweets = api.user_timeline(screen_name = screen_name, count=10, tweet_mode="extended")
    tweet = new_tweets[0] # An object of class Status (tweepy.models.Status)
    print(tweet.full_text) # Print the text of the tweet

    # print(f"\n User @handle: {screen_name}", f"\n User ID: {user_id}", f"\n User access token: {access_token}", f" \n User access token secret: {access_token_secret} \n")
