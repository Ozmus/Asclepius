import sys
import requests
from requests_oauthlib import OAuth1Session
import tweepy
import os
from dotenv import load_dotenv


load_dotenv()
CONSUMER_KEY = os.getenv('TWITTER_API_KEY')
CONSUMER_SECRET = os.getenv('TWITTER_API_KEY_SECRET')

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

def get_user_authorization(resource_owner_oauth_token):

    authorization_url = f"https://api.twitter.com/oauth/authorize?oauth_token={resource_owner_oauth_token}"
    authorization_pin = input(f" \n Send the following URL to the user you want to generate access tokens for. \n → {authorization_url} \n "
                              f"This URL will allow the user to authorize your application and generate a PIN. \n Paste PIN here: ")

    return(authorization_pin)

def get_user_access_tokens(resource_owner_oauth_token, resource_owner_oauth_token_secret, authorization_pin):

    oauth = OAuth1Session(  CONSUMER_KEY,
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

def authorizationTwitter():
    resource_owner_oauth_token, resource_owner_oauth_token_secret = request_token()
    authorization_url = f"https://api.twitter.com/oauth/authorize?oauth_token={resource_owner_oauth_token}"
    return resource_owner_oauth_token, resource_owner_oauth_token_secret, authorization_url

def getTweets(resource_owner_oauth_token, resource_owner_oauth_token_secret, authorization_pin):
    access_token, access_token_secret, user_id, screen_name = get_user_access_tokens(
        resource_owner_oauth_token, resource_owner_oauth_token_secret, authorization_pin)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    new_tweets = api.user_timeline(screen_name = screen_name, count=10, tweet_mode="extended")
    return new_tweets

