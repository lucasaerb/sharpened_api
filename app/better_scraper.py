from json import loads
from langchain.text_splitter import RecursiveCharacterTextSplitter
from trafilatura.downloads import fetch_url
from trafilatura.core import extract

def scrape_urls(urls):
    print("Scraping urls...", urls)
    extracted_content = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    metadata_list = []

    #deduplicate urls
    # urls = remove_duplicates_preserve_order(urls)

    for url in urls:
        # try:
        #     html = requests.get(url, headers=headers)
        #     html_text, title_text = text_from_html(html.text)
        # except Exception as e:
        #     print("Error: ", e)
        #     continue


        # below code for trafilatura

        try:
            if url:
                downloaded = fetch_url(url)
                response = extract(downloaded, url, with_metadata=True, output_format="json")
                # print(response)
                if response:
                    # print(response)
                    response = loads(response)
                    extracted_content.append(response['raw_text'])
                    if response['title']:
                        metadata_list.append({"source": url, "title": response['title']})
                    else:
                        metadata_list.append({"source": url, "title": "None"})
        except Exception as e:
            print("Could not extract content from: ", url, "Error: ", e)
            continue

        #### Below code for normal requests

        # if html_text and len(html_text) > 500:
        #     extracted_content.append(html_text)
        #     if title_text:
        #         metadata_list.append({"source": url, "title": title_text})
        #     else:
        #         metadata_list.append({"source": url, "title": "None"})
        # else:
        #     print("Could not extract content from: ", url)



    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=400, chunk_overlap=50
    )

    documents = splitter.create_documents(extracted_content, metadata_list)
    splits = splitter.split_documents(documents)

    result = []
    for split in splits:
        if (split and len(split.page_content) > 100):
            result.append({'content':split.page_content, 'url': split.metadata["source"], 'title': split.metadata["title"]})
        else:
            print("Could not extract content from: ", split.metadata["source"], "text too short.")
    # returns a list of dictionaries with keys: content, url, title
    return result
