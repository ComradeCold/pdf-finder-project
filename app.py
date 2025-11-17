from flask import Flask, request, render_template
import os
import requests
from google.cloud import vision

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY")
CX = os.environ.get("CX")


def google_pdf_search(query, num_results=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": f"{query} filetype:pdf",
        "key": API_KEY,
        "cx": CX,
        "num": num_results,
    }
    try:
        response = requests.get(url, params=params).json()

        if response.get("error"):
            return {"error": f"Google Search API Error: {response['error']['message']}"}

        return [
            item["link"] for item in response.get("items", []) if item["link"].endswith(".pdf")
        ]
    except requests.RequestException as e:
        return {"error": f"Network Error connecting to Google Search API: {e}"}
    except Exception as e:
        return {"error": f"Unexpected search error: {e}"}


def extract_text_from_image(file):
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=file.read())
        response = client.text_detection(image=image)

        if response.error.message:
            return {"error": f"Google Vision API Error: {response.error.message}"}

        if response.text_annotations:
            return response.text_annotations[0].description

        return ""
    except Exception as e:
        return {"error": f"Unexpected OCR error: {e}"}


@app.route("/", methods=["GET", "POST"])
def home():
    pdfs = []
    extracted_text = ""
    query = ""
    error_message = None

    if request.method == "POST":
        try:
            query = request.form.get("query", "")
            uploaded_image = request.files.get("image")

            if uploaded_image:
                result = extract_text_from_image(uploaded_image)
                if isinstance(result, dict):
                    error_message = result["error"]
                else:
                    extracted_text = result

            if not error_message:
                final_query = f"{query} {extracted_text}".strip()
                if final_query:
                    result = google_pdf_search(final_query)
                    if isinstance(result, dict):
                        error_message = result["error"]
                    else:
                        pdfs = result

        except Exception as e:
            error_message = f"Internal server error: {e}"

    if error_message:
        return render_template("error.html", error_message=error_message)

    return render_template("index.html", pdfs=pdfs, query=query)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

