import requests

API_KEY = "AIzaSyDwt1L88Bvggia6xwbz8FGf113JS8hX6Ig"
CX = "35983c876ba0c4339"

def google_pdf_search(query, num_results=10):
    print(f"Searching Google for PDFs related to: {query}")
    results = []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": f"{query} filetype:pdf",
        "key": API_KEY,
        "cx": CX,
        "num": 10
    }

    try:
        response = requests.get(url, params=params).json()
        if "items" in response:
            for item in response["items"]:
                link = item.get("link", "")
                if link.lower().endswith(".pdf") or ".pdf" in link.lower():
                    results.append(link)
        else:
            print("No results from Google API:", response.get("error", response))
    except Exception as e:
        print("Error:", e)

    return results


if __name__ == "__main__":
    query = input("Enter a topic to search for PDFs: ")
    pdfs = google_pdf_search(query)
    if pdfs:
        print("\nFound PDF links:")
        for link in pdfs:
            print(link)
    else:
        print("\nNo PDF links found. Try different keywords.")

