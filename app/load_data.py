import datetime
from json import load, dumps
import requests
from langchain_openai import OpenAIEmbeddings
from app.local_creds import *

# negligible change in the code
#To do: add logger
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

request_url = f"https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/json/v1/{ASTRA_DB_NAMESPACE}/chat"
request_headers = { 'x-cassandra-token': ASTRA_DB_APPLICATION_TOKEN,  'Content-Type': 'application/json'}

def get_input_data():
    scraped_results_file = INPUT_DATA
    with open(scraped_results_file) as f:
        scraped_data = load(f)
    return scraped_data

def embed(text_to_embed):
    embedding = list(embeddings.embed_query(text_to_embed))
    return embedding


# def add_docs_to_db(docs, user_id):
#     # docs should be a list of dictionaries with keys: url, title, content
#     i = 0
#     documents = []
#     for doc in docs:
        
#         # print(doc)
#         document_id = doc["url"]
#         document_title = doc["title"]
#         document_content = doc["content"]
#         text_to_embed = f"{document_content}"
#         embedding = embed(text_to_embed)
#         current_time = datetime.datetime.now().isoformat()
#         json_data = {"timestamp": current_time}
#         to_insert = {"user_id": user_id, "json_data": json_data, "document_id": document_id, "document_title": document_title, "document_content": document_content, "$vector": embedding}
#         documents.append(to_insert)
#         # to_insert = {"insertOne": {"document": {"user_id": user_id, "json_data": json_data, "document_id": document_id, "document_title": document_title, "document_content": document_content, "$vector": embedding}}}
#         # response = requests.request("POST", request_url, headers=request_headers, data=dumps(to_insert))
#         i += 1
    
#     response = requests.request("POST", request_url, headers=request_headers, data=dumps({"insertMany": {"documents": documents}}))
#     # print(response.text + "\t Count: "+str(i))

#     return i

def add_docs_to_db(docs, user_id):
    # docs should be a list of dictionaries with keys: url, title, content
    total = 0
    documents = []
    print("adding docs to datastax astra: ", len(docs))
    for doc in docs:
        if doc and doc["content"]:
            document_id = doc["url"]
            document_title = doc["title"]
            document_content = doc["content"]
            text_to_embed = f"URL:{document_id} title:{document_title} content:{document_content}"
            print("about to embed")
            embedding = embed(text_to_embed)
            print("there must be an error here somewhere?")
            current_time = datetime.datetime.now().isoformat()
            json_data = {"timestamp": current_time}
            to_insert = {"user_id": user_id, "json_data": json_data, "document_id": document_id, "document_title": document_title, "document_content": document_content, "$vector": embedding }
            documents.append(to_insert)
            print("doc appended. total: ", total)
            # to_insert = {"insertOne": {"document": {"user_id": user_id, "json_data": json_data, "document_id": document_id, "document_title": document_title, "document_content": document_content, "$vector": embedding}}}
            # response = requests.request("POST", request_url, headers=request_headers, data=dumps(to_insert))
            total += 1
        
    # step = 10
    # for i in range(0, len(documents), step):
    #     try:
    #         response = requests.request("POST", request_url, headers=request_headers, data=dumps({"insertMany": {"documents": documents[i:i+step]}}))
    #         if response:
    #             print("response status: ", str(response.status_code),  "\t Inserted Count: ", str(i))
    #         else:
    #             print("no response: ", response)
    #     except Exception as e:
    #         print("Error exception:",e)
    #         continue

    step = 10
    print("or perhaps this threadPool is the issue?")
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i in range(0, len(documents), step):
            future = executor.submit(send_request, i, documents, step)
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            # Process the result if needed

    return total




def send_request(i, documents, step):
    try:
        print(f'insertMany documents[{i}:{i+step}]')
        response = requests.request("POST", request_url, headers=request_headers, data=dumps({"insertMany": {"documents": documents[i:i+step]}}))
        if response:
            print("response status: ", str(response.status_code),  "\t Inserted Count: ", str(i))
        else:
            print("no response: ", response)
    except Exception as e:
        print("Error exception:",e)




def add_urls_to_db(urls, user_id):
    # docs should be a list of dictionaries with keys: url, title, content
    total = 0
    documents = []
    print("adding urls to datastax astra: ", urls)
    for url in urls:
        if url:
            document_id = url
            document_title = "None"
            document_content = "None"
            embedding = []
            current_time = datetime.datetime.now().isoformat()
            json_data = {"timestamp": current_time}
            to_insert = {"user_id": user_id, "json_data": json_data, "document_id": document_id, "document_title": document_title, "document_content": document_content, "$vector": embedding }
            documents.append(to_insert)
            # to_insert = {"insertOne": {"document": {"user_id": user_id, "json_data": json_data, "document_id": document_id, "document_title": document_title, "document_content": document_content, "$vector": embedding}}}
            # response = requests.request("POST", request_url, headers=request_headers, data=dumps(to_insert))
            total += 1
    try:
        step = 10
        for i in range(0, len(documents), step):
            response = requests.request("POST", request_url, headers=request_headers, data=dumps({"insertMany": {"documents": documents[i:i+step]}}))
            print("response status: ", str(response.status_code),  "\t Inserted Count: ", str(i))
    except Exception as e:
        print("Error exception:",e)
    return total

def main():
    input_data_faq = get_input_data()
    add_docs_to_db(input_data_faq, user_id="000")
    


if __name__ == "__main__":
    main()
