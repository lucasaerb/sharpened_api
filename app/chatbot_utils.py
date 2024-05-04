from app.local_creds import *
from app.load_data import *

from langchain.prompts import PromptTemplate
from json import dumps
import requests
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

request_url = f"https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/json/v1/{ASTRA_DB_NAMESPACE}/chat"
request_headers = { 'x-cassandra-token': ASTRA_DB_APPLICATION_TOKEN,  'Content-Type': 'application/json'}

# langchain openai interface
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY)
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY) 

def get_similar_docs(query, user_id, number):
    # print("request_URL: ", request_url)
    # print("request_headers: ", request_headers)
    # print(query)
    try:
        embedding = list(embedding_model.embed_query(query))
    except Exception as e:
        print(e)
        return None, None

    # embedding = embedding_model.embed_query(query)
    payload = dumps({"find": {"sort": {"$vector": embedding},"options": {"includeSimilarity" : True, "limit": number}, "filter": {"user_id" : user_id}} })
    # print(payload)
    # need to handle the case where there are no relevant docs below to return. NONE
    relevant_docs = requests.request("POST", request_url, headers=request_headers, data=payload).json()
    # print("\n\n\nrelevant docs:", relevant_docs['data'])
    relevant_docs = relevant_docs['data']['documents']
    if len(relevant_docs) == 0:
        return None, None
    docs_contents = [row['document_content'] for row in relevant_docs] 
    docs_urls = [row['document_id'] for row in relevant_docs]
    docs_similarities = [row['$similarity'] for row in relevant_docs]
    print("\n\n\n similarities:", docs_similarities)

    result_contents = []
    result_urls = []
    i=0
    for i, doc in enumerate(docs_contents):
        if docs_similarities[i] >= 0.87:
            result_contents.append(doc)
            result_urls.append(docs_urls[i])
    if len(result_contents) == 0:
        return None, None
    return result_contents, result_urls

def remove_duplicates_preserve_order(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def get_docs_from_db(user_id):
    print("getting docs from db")
    try:
        embedding = list(embedding_model.embed_query("Get any docs from the database for this user."))
    except Exception as e:
        print(e)
        return None, None
    # embedding = embedding_model.embed_query()
    payload = dumps({"find": {"sort": {"$vector": embedding},"options": { "limit": 1000}, "filter": {"user_id" : user_id}} })
    # print(payload)
    # need to handle the case where there are no relevant docs below to return. NONE
    response = requests.request("POST", request_url, headers=request_headers, data=payload).json()
    if (response and ('data' in response)):
        relevant_docs = response['data']['documents']
        if len(relevant_docs) == 0:
            return None, None
    # docs_contents = [row['document_content'] for row in relevant_docs]
        docs_titles = [row['document_title'] for row in relevant_docs]
        docs_urls = [row['document_id'] for row in relevant_docs]
    # docs_similarities = [row['$similarity'] for row in relevant_docs]
    # print("\n\n\n similarities:", docs_similarities)
    # print("getting docs from db", docs_contents, docs_urls)

    # docs_titles = list(set(docs_titles))
    # docs_urls = list(set(docs_urls)) // causes problems. Need to remove duplicates while preserving order

        docs_titles = remove_duplicates_preserve_order(docs_titles)
        docs_urls = remove_duplicates_preserve_order(docs_urls)
        print("got docs from db", docs_titles, docs_urls)
        return docs_titles, docs_urls
    return None, None
# prompt that is sent to openai using the response from the vector database and the users original query
prompt_boilerplate = "Answer the question posed in the user query section using the provided context. If you don't know the answer, just say that you don't know, don't try to make up an answer. Also remark on whether the provided context was useful in generating the answer and why. Include sources for any information you provide."
user_query_boilerplate = "USER QUERY: {userQuery}"
document_context_boilerplate = "CONTEXT: {documentContext}"
final_answer_boilerplate = "Final Answer: "

def build_full_prompt(query, user_id):
    relevant_docs, urls = get_similar_docs(query, user_id, 10)
    if relevant_docs is None:
        return None, None
    docs_single_string = "\n".join(relevant_docs)
    # if urls:
    #     url = urls[0] # set(urls)
    # else:
    #     url = "No relevant documents found"


    nl = "\n"
    combined_prompt_template = PromptTemplate.from_template(prompt_boilerplate + nl + user_query_boilerplate + nl + document_context_boilerplate + nl + final_answer_boilerplate)
    filled_prompt_template = combined_prompt_template.format(userQuery=query, documentContext=docs_single_string)
    # print(filled_prompt_template)
    return filled_prompt_template, urls


def send_to_openai(full_prompt):
    return llm.predict(full_prompt)


# # add document to the database
# def add_document_to_db(urls_list):
#     print("scraping urls")
#     docs = scrape_urls(urls_list)
#     print("adding docs to db")
#     response = add_docs_to_db(docs)
#     return f"{response} docs were successfully added to the database.", docs
