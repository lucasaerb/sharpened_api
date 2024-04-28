from json import loads, dumps
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from bs4 import BeautifulSoup
# from bs4.element import Comment
import requests
from trafilatura import fetch_url, extract


# def tag_visible(element):
#     if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
#         return False
#     if isinstance(element, Comment):
#         return False
#     return True


# def text_from_html(body):
#     soup = BeautifulSoup(body, 'html.parser')

#     # get text
#     text = soup.get_text()
#     title = soup.title.string if soup.title else "None"
#     for script in soup(["script", "style"]):
#         script.extract()    # rip it out
#     # break into lines and remove leading and trailing space on each
#     lines = (line.strip() for line in text.splitlines())
#     # break multi-headlines into a line each
#     chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
#     # drop blank lines
#     text = ''.join(chunk for chunk in chunks if chunk)


#     return text, title


# def remove_duplicates_preserve_order(seq):
#     seen = set()
#     seen_add = seen.add
#     return [x for x in seq if not (x in seen or seen_add(x))]

# currently only works with blogs and text does not extract reddit or twitter or other social media
# need to add support for those

def scrape_urls(urls):
    print("Scraping urls...", urls) #URLS is presently a LIST of LISTS... I think. Need to check.
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
        downloaded = fetch_url(url)
        response = extract(downloaded, with_metadata=True, output_format="json")
        print(response)
        if response:
            # print(response)
            response = loads(response)
            extracted_content.append(response['raw_text'])
            if response['title']:
                metadata_list.append({"source": url, "title": response['title']})
            else:
                metadata_list.append({"source": url, "title": "None"})

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
            chunk_size=500, chunk_overlap=50
    )

    documents = splitter.create_documents(extracted_content, metadata_list)
    splits = splitter.split_documents(documents)

    result = []
    for split in splits:
        if len(split.page_content) > 100:
            result.append({'content':split.page_content, 'url': split.metadata["source"], 'title': split.metadata["title"]})
        else:
            print("Could not extract content from: ", split.metadata["source"], "text too short.")
    # returns a list of dictionaries with keys: content, url, title
    return result



# def main():
#     urls = ["https://www.wsj.com",  "https://docs.datastax.com/en/dse68-security/docs/secFAQ.html", "https://www.reddit.com/r/LangChain/comments/18wzh73/rag_demo_cheapest_way_to_host/?utm_source=pocket_list", "https://twitter.com/adcock_brett/status/1743987597301399852?utm_source=pocket_list", "https://jenni.ai/?utm_source=pocket_list", "https://abcnews.go.com/International/virgin-atlantic-makes-maiden-transatlantic-flight-100-green/story?id=105206806&utm_source=pocket_list", "https://www.databricks.com/resources/demos/tutorials/data-science-and-ai/lakehouse-ai-deploy-your-llm-chatbot?utm_source=pocket_list", "https://www.reddit.com/r/LangChain/comments/18wzh73/rag_demo_cheapest_way_to_host/?utm_source=pocket_list", "https://twitter.com/adcock_brett/status/1743987597301399852?utm_source=pocket_list", "https://jenni.ai/?utm_source=pocket_list", "https://abcnews.go.com/International/virgin-atlantic-makes-maiden-transatlantic-flight-100-green/story?id=105206806&utm_source=pocket_list", "https://www.databricks.com/resources/demos/tutorials/data-science-and-ai/lakehouse-ai-deploy-your-llm-chatbot?utm_source=pocket_list",  "https://www.wsj.com", ]
#     write_to_file = scrape_urls(urls)

#     # print(write_to_file)

#     with open("scraped_results.json", "w") as f:
#         f.write(dumps(write_to_file))


# if __name__ == "__main__":
#     main()