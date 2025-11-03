from flask import Flask, request, render_template_string
import requests
import os

app = Flask(__name__)

#API_KEY = os.environ.get("AIzaSyDwt1L88Bvggia6xwbz8FGf113JS8hX6Ig")
#CX = os.environ.get("35983c876ba0c4339")
API_KEY = "AIzaSyDwt1L88Bvggia6xwbz8FGf113JS8hX6Ig"
CX = "35983c876ba0c4339"

def google_pdf_search(query, num_results=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": f"{query} filetype:pdf", "key": API_KEY, "cx": CX, "num": num_results}
    pdf_links = []
    try:
        response = requests.get(url, params=params).json()
        print(response) 
        if "items" in response:
            for item in response["items"]:
                link = item.get("link", "")
                if ".pdf" in link.lower():
                    pdf_links.append(link)
        else:
            print("No results from Google API:", response.get("error", response))
    except Exception as e:
        print("Error during API request:", e)
    return pdf_links


@app.route("/", methods=["GET", "POST"])
def home():
    pdfs = []
    query = ""
    if request.method == "POST":
        query = request.form.get("query")
        if query:
            pdfs = google_pdf_search(query)

    
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>PDF Finder</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        input[type=text] { width: 400px; padding: 8px; }
        input[type=submit] { padding: 8px 12px; }
        .results { margin-top: 20px; border: 1px solid #ccc; padding: 15px; max-width: 700px; background: #f9f9f9; }
        .results ul { list-style-type: none; padding-left: 0; }
        .results li { margin-bottom: 8px; }
        .raw { margin-top: 20px; background: #eef; padding: 10px; border: 1px solid #99c; }
    </style>
</head>
<body>
    <h1>PDF Finder</h1>
    <form method="post">
        <input type="text" name="query" placeholder="Enter search term" value="{{query}}" required>
        <input type="submit" value="Search">
    </form>

    {% if pdfs %}
        <div class="results">
            <h2>PDF Results:</h2>
            <ul>
                {% for pdf in pdfs %}
                    <li><a href="{{pdf}}" target="_blank">{{pdf}}</a></li>
                {% endfor %}
            </ul>
        </div>

        <div class="raw">
            <h3>Raw PDF List:</h3>
            <pre>{{ pdfs }}</pre>
        </div>
    {% elif query %}
        <p>No PDFs found for "<strong>{{query}}</strong>"</p>
    {% endif %}
</body>
</html>
"""

    return render_template_string(html, pdfs=pdfs, query=query)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
