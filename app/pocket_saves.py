from json import dumps
import json
from time import sleep
import requests
from langchain_openai import OpenAIEmbeddings
from app.load_data import *
from app.better_scraper import *
import sys
import concurrent.futures

sys.path.append("utils")
from app.local_creds import *
#To do: add logger
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# request_url = f"https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/json/v1/{ASTRA_DB_NAMESPACE}/chat"
# request_headers = { 'x-cassandra-token': ASTRA_DB_APPLICATION_TOKEN,  'Content-Type': 'application/json'}



def get_pocket_saves(pocket_access_token, offset):
    request_url = f"https://getpocket.com/v3/get"
    request_headers = { 'Content-Type': 'application/json', 'X-Accept': 'application/json'}
    request_data = {"consumer_key": POCKET_CONSUMER_KEY, "access_token": pocket_access_token, "count": int(POCKET_REQUEST_COUNT), "offset": offset, "detailType": "simple"}
    response = requests.request("POST", request_url, headers=request_headers, data=dumps(request_data))
    try:
        result = response.json()
    except:
        # print(response)
        return None
    return result


def obtain_request_token():
    request_url = f"https://getpocket.com/v3/oauth/request"
    request_headers = { 'Content-Type': 'application/json', 'X-Accept': 'application/json'}
    request_data = {"consumer_key": POCKET_CONSUMER_KEY, "redirect_uri": "https://sharpened.vercel.app/"}
    response = requests.request("POST", request_url, headers=request_headers, data=dumps(request_data))
    try:
        request_token = response.json()
    except:
        return None
    return request_token['code']

def obtain_access_token(request_token):
    request_url = f"https://getpocket.com/v3/oauth/authorize"
    request_headers = { 'Content-Type': 'application/json', 'X-Accept': 'application/json'}
    request_data = {"consumer_key": POCKET_CONSUMER_KEY, "code": request_token}
    response = requests.request("POST", request_url, headers=request_headers, data=dumps(request_data))
    try:
        access_token = response.json()
    except:        
        return None

    # will want to save this access token from the user so it can be used again... maybe every request from a user uses this same access token
    return access_token['access_token']

# Python for the authentication process below
# def authenticate_pocket():
#     request_token = obtain_request_token()

#     print(request_token['code'])

#     # redirect user to https://getpocket.com/auth/authorize?request_token=REQUEST_TOKEN&redirect_uri=REDIRECT_URI
#     redirect = f"https://getpocket.com/auth/authorize?request_token={request_token['code']}&redirect_uri=sharpened.vercel.app"

#     # user authenticates and is redirected to redirect_uri
#     # wait for user to be redirected to redirect_uri


#     # convert request token to access token
#     access_token = obtain_access_token(request_token)
#     print(access_token)


def load_saves_into_db(access_token, user_id):
    url_list = get_urls_from_pocket(access_token, user_id)
    content = scrape_urls(url_list) #returns a list of dictionaries with keys: url, title, content
    total_count = add_docs_to_db(content, user_id)
    print("url_list: ", url_list)
    print (f"{total_count} Pocket saves successfully loaded into database.")
    return {"text": f"Success: {total_count} Pocket saves loaded into database"}

def add_to_db_given_urls(url_list, user_id):
    content = scrape_urls(url_list) #returns a list of dictionaries with keys: url, title, content
    total_count = add_docs_to_db(content, user_id)
    # print("url_list: ", url_list)
    print (f"{total_count} Pocket saves successfully loaded into database.")
    return {"text": f"Success: {total_count} Pocket saves loaded into database"}

# def get_urls_from_pocket(access_token, user_id):
#     result = []
#     offset = 0
#     total_count = 0
#     while offset < 1000:
#         saves = get_pocket_saves(access_token, offset)
#         print("SAVES type: ", type(saves), "saves[list] type:", type(saves['list']))
#         if saves is None or len(saves['list']) == 0:
#             return result
#         try:
#             url_list = [item['given_url'] for item in saves['list'].values()]
#             result.extend(url_list)
#         except Exception as e:
#             print("Error getting urls from pocket: ", e)
#         offset += int(POCKET_REQUEST_COUNT)
#     return result

def get_urls_from_pocket(access_token, user_id):
    result = []
    offsets = range(0, 1000, int(POCKET_REQUEST_COUNT))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(get_pocket_saves, access_token, offset): offset for offset in offsets}
        for future in concurrent.futures.as_completed(future_to_url):
            offset = future_to_url[future]
            try:
                saves = future.result()
                print("SAVES type: ", type(saves), "saves[list] type:", type(saves['list']))
                if saves is not None and len(saves['list']) > 0:
                    url_list = [item['resolved_url'] for item in saves['list'].values()]
                    result.extend(url_list)
            except Exception as e:
                print("Error getting urls from pocket at offset {}: {}".format(offset, e))

    return result

def main():
    request_token = obtain_request_token()
    print('request_token:', request_token)
    # user then authenticates at the url below
    print(f"redirect: https://getpocket.com/auth/authorize?request_token={request_token}&redirect_uri=https://sharpened.vercel.app")
    sleep(12)
    access_token = obtain_access_token(request_token)
    print("access_token", access_token)

    res = get_pocket_saves(access_token)

    print(res)
    
#    redirect = f"https://getpocket.com/auth/authorize?request_token=5197f9a5-62bd-c1cd-9793-b7a556&redirect_uri=sharpened.vercel.app"


if __name__ == "__main__":
    main()
