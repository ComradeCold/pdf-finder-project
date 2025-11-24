from flask import Flask, request, render_template, jsonify
import os
import requests
import pymysql
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

def get_db_config():
    # Check if we're in Cloud Run environment
    if os.environ.get('K_SERVICE'):  # Cloud Run environment variable
        # Use Cloud SQL Proxy connection
        db_config = {
            'unix_socket': '/cloudsql/cs446-finalproject-group-7:us-central1:pdf-finder-db',
            'user': 'appuser',
            'password': 'Ajiefw9340*',
            'database': 'pdf_finder',
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    else:
        # Local development connection
        db_config = {
            'host': '34.66.54.180',
            'user': 'appuser',
            'password': 'Ajiefw9340*',
            'database': 'pdf_finder',
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    return db_config

config = get_db_config()

def store_click(link_url):
    try:
        print(f"Attempting to store click for: {link_url}")

        # Test database connection first
        cnx = pymysql.connect(**config)
        print("Database connection successful")

        cursor = cnx.cursor()

        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'pdf_clicks'")
        table_exists = cursor.fetchone()
        print(f"Table exists: {table_exists}")

        if not table_exists:
            print("pdf_clicks table doesn't exist! Creating it...")
            cursor.execute("""
                CREATE TABLE pdf_clicks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    link_url VARCHAR(2083) NOT NULL,
                    click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cnx.commit()
            print("Created pdf_clicks table")

        # Check if the link already exists
        cursor.execute("SELECT id FROM pdf_clicks WHERE link_url = %s", (link_url,))
        exists = cursor.fetchone()
        print(f"Link exists check: {exists}")

        if not exists:
            cursor.execute("INSERT INTO pdf_clicks (link_url) VALUES (%s)", (link_url,))
            cnx.commit()
            print(f"Successfully stored new link: {link_url}")
            result = True
        else:
            print(f"ℹLink already exists: {link_url} (ID: {exists[0]})")
            result = True

        cursor.close()
        cnx.close()
        return result

    except pymysql.Error as e:
        print(f"MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


@app.post("/api/click")
def api_click():
    try:
        data = request.get_json()
        print(f"Received data: {data}")

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        link = data.get("link_url")
        print(f"Received click request for: {link}")

        if not link:
            return jsonify({"error": "Missing link_url"}), 400

        success = store_click(link)

        if success:
            return jsonify({"status": "ok", "saved": link})
        else:
            return jsonify({"error": "Failed to store click"}), 500

    except Exception as e:
        print(f"API Error: {e}")
        import traceback
        print(f"API Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/test-db")
def test_db():
    try:
        print("Testing database connection...")
        cnx = pymysql.connect(**config)
        print("Database connection successful")

        cursor = cnx.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"Database query test: {result}")

        cursor.close()
        cnx.close()
        return jsonify({"status": "success", "message": "Database connection working"})

    except Exception as e:
        print(f"Database connection failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

