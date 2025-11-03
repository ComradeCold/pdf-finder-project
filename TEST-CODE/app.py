from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_KEY = "AIzaSyDwt1L88Bvggia6xwbz8FGf113JS8hX6Ig"
CX = "35983c876ba0c4339"

def google_pdf_search(query, num_results=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": f"{query} filetype:pdf","key": API_KEY,"cx": CX,"num": 10}
    pdf_links = []
    response = requests.get(url, params=params).json()
    for item in response.get("items", []):
        link = item.get("link", "")
        if ".pdf" in link.lower():
            pdf_links.append(link)
    return pdf_links

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    pdfs = google_pdf_search(query)
    return jsonify({"results": pdfs})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

