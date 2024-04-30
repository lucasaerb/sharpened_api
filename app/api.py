from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.chatbot_utils import *
from app.pocket_saves import *
from json import dumps
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3000/saves",
    "https://sharp-ten.vercel.app"
    "https://sharp-ten.vercel.app/saves"
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Query(BaseModel):
    prompt: str
    user_id: str

class User(BaseModel):
    user_id: str

class ReqToken(BaseModel):
    request_token: str

class AccessToken(BaseModel):
    access_token: str
    user_id: str

class DocList(BaseModel):
    urls: list[str]
    user_id: str

@app.post("/api/chat")
async def fill_and_send_prompt(query: Query):
    if query.prompt is None or query.prompt == "":
        return dumps({"text": "No prompt provided"})
    docs, urls = build_full_prompt(query.prompt, query.user_id)
    if docs is None:
        return dumps({"text": "No relevant documents found for that query. Please be more specific."})
    return dumps({"text": send_to_openai(docs), "urls" : urls})


@app.post("/api/vector_search")
async def vector_search(query: Query):
    if query.prompt is None or query.prompt == "":
        return dumps({"text": "No prompt provided"})
    relevant_docs, urls = get_similar_docs(query.prompt, query.user_id, 10)
    if relevant_docs is None:
        return dumps({"text": "No relevant documents found for that query. Please be more specific."})
    return dumps({"docs": relevant_docs, "urls": urls})


# @app.post("/api/add_documents")
# async def send_document(doclist: DocList):
#     response, docs = add_document_to_db(doclist.urls) #should be a url to add, need to update to list of urls
#     return json.dumps({"text": response, "docs": docs})

@app.post("/api/authenticate_pocket")
async def authenticate_with_pocket(query: Query):
    request_token = obtain_request_token()
    return dumps({"request_token": request_token})

@app.post("/api/finish_authenticate_pocket")
async def authenticate_with_pocket_complete(token: ReqToken):
    access_token = obtain_access_token(token.request_token)
    return dumps({"access_token": access_token})

@app.post("/api/load_pocket_saves_into_db")
async def load_pocket_saves(token: AccessToken, background_tasks: BackgroundTasks):
    if token.access_token is None:
        return dumps({"text": "Error loading pocket saves. No access token provided."})
    if token.user_id is None:
        return dumps({"text": "Error loading pocket saves. No user id provided."})
    background_tasks.add_task(load_saves_into_db, token.access_token, token.user_id)
    return dumps({"text": "Loading pocket saves into database."})

@app.post("/api/get_pocket_saves")
async def load_pocket_saves(token: AccessToken):
    if token.access_token is None:
        return dumps({"text": "Error loading pocket saves. No access token provided."})
    if token.user_id is None:
        return dumps({"text": "Error loading pocket saves. No user id provided."})
    urls_list = get_urls_from_pocket(token.access_token, token.user_id)
    print("urls_list returned: ", urls_list)
    # add_urls_to_db(urls_list, token.user_id)
    return dumps({"text": "Retrieved urls from pocket.", "urls": urls_list})

@app.post("/api/add_urls_to_db")
async def add_urls(docs: DocList, background_tasks: BackgroundTasks):
    if docs.urls is None:
        return dumps({"text": "Error loading pocket saves. No urls list provided."})
    if docs.user_id is None:
        return dumps({"text": "Error loading pocket saves. No user id provided."})
    urls_list = docs.urls
    if len(urls_list) > 10:
        return dumps({"text": "Error loading pocket saves. Too many urls provided. Please add up to 10."})
    add_to_db_given_urls(urls_list, docs.user_id)
    return dumps({"text": "Loading urls into database.", "urls": urls_list})

@app.post("/api/get_docs_from_db")
async def get_docs(user: User):
    print("getting docs from db")
    if user.user_id is None:
        return dumps({"text": "Error loading docs from db. No user id provided."})
    # convert this to a set
    docs_titles, urls_list = get_docs_from_db(user.user_id)
    print("type of docs titles", type(docs_titles))
    return dumps({"titles": docs_titles, "urls": urls_list})


# @app.post("/api/remove_documents")
# async def remove_document(doclist: DocList):
#     response = remove_document_from_db(doclist.urls)
#     return json.dumps({"text": response})