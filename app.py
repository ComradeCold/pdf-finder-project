from flask import Flask, request, render_template, jsonify
import os
import requests
import pymysql
from google.cloud import vision

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY")
CX = os.environ.get("CX")

# search API for PDF links
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

# extracts text from user input image
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

# loads favorited pdf links from database
def get_favorites():
    try:
        cnx = pymysql.connect(**config)
        cursor = cnx.cursor()

        cursor.execute("""
            SELECT link_url, favorited_at 
            FROM pdf_favorites 
            ORDER BY favorited_at DESC
        """)

        favorites = cursor.fetchall()
        cursor.close()
        cnx.close()

        formatted_favorites = []
        for fav in favorites:
            link_url = fav[0]
            favorited_at = fav[1]

            if favorited_at:
                formatted_time = favorited_at.strftime('%Y-%m-%d %H:%M')
            else:
                formatted_time = 'Recently'

            formatted_favorites.append((link_url, formatted_time))

        return formatted_favorites
    except Exception as e:
        return []

# homepage
@app.route("/", methods=["GET", "POST"])
def home():
    pdfs = []
    extracted_text = ""
    query = ""
    error_message = None

    favorites = get_favorites()

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

    return render_template("index.html", pdfs=pdfs, query=query, favorites=favorites)

# database configurations
def get_db_config():
    if os.environ.get('K_SERVICE'):
        db_config = {
            'unix_socket': '/cloudsql/cs446-finalproject-group-7:us-central1:pdf-finder-db',
            'user': os.environ.get('DB_USER', 'appuser'),
            'password': os.environ.get('DB_PASSWORD', 'Ajiefw9340*'),
            'database': os.environ.get('DB_NAME', 'pdf_finder'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    else:
        db_config = {
            'host': os.environ.get('DB_HOST', '34.66.54.180'),
            'user': os.environ.get('DB_USER', 'appuser'),
            'password': os.environ.get('DB_PASSWORD', 'Ajiefw9340*'),
            'database': os.environ.get('DB_NAME', 'pdf_finder'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    return db_config

config = get_db_config()

# stores users' pdf link clicks in SQL database table
def store_click(link_url):
    try:
        cnx = pymysql.connect(**config)
        cursor = cnx.cursor()

        cursor.execute("SHOW TABLES LIKE 'pdf_clicks'")
        table_exists = cursor.fetchone()

        if not table_exists:
            cursor.execute("""
                CREATE TABLE pdf_clicks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    link_url VARCHAR(2083) NOT NULL,
                    click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cnx.commit()

        cursor.execute("SELECT id FROM pdf_clicks WHERE link_url = %s", (link_url,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("INSERT INTO pdf_clicks (link_url) VALUES (%s)", (link_url,))
            cnx.commit()
            result = True
        else:
            result = True
            
        cursor.close()
        cnx.close()
        return result

    except Exception:
        return False

# saves pdf to favorites SQL table
def store_favorite(link_url):
    try:
        cnx = pymysql.connect(**config)
        cursor = cnx.cursor()

        cursor.execute("SELECT id FROM pdf_favorites WHERE link_url = %s", (link_url,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("INSERT INTO pdf_favorites (link_url) VALUES (%s)", (link_url,))
            cnx.commit()
            result = True
        else:
            result = True

        cursor.close()
        cnx.close()
        return result

    except Exception:
        return False

# removes pdf from favorites
def remove_favorite(link_url):
    try:
        cnx = pymysql.connect(**config)
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM pdf_favorites WHERE link_url = %s", (link_url,))
        cnx.commit()
        
        cursor.close()
        cnx.close()
        return True

    except Exception:
        return False

# log pdf clicks
@app.post("/api/click")
def api_click():
    try:
        data = request.get_json()
        link = data.get("link_url")

        if not link:
            return jsonify({"error": "Missing link_url"}), 400

        success = store_click(link)

        if success:
            return jsonify({"status": "ok", "saved": link})
        else:
            return jsonify({"error": "Failed to store click"}), 500

    except Exception:
        return jsonify({"error": "Internal server error"}), 500

# favorites: add or remove the pdf link
@app.post("/api/favorite")
def api_favorite():
    try:
        data = request.get_json()
        link = data.get("link_url")
        action = data.get("action", "add")

        if not link:
            return jsonify({"error": "Missing link_url"}), 400

        if action == "remove":
            success = remove_favorite(link)
        else:
            success = store_favorite(link)

        if success:
            return jsonify({
                "status": "ok",
                "favorited": link,
                "action": action
            })
        else:
            return jsonify({"error": "Failed to save favorite"}), 500

    except Exception:
        return jsonify({"error": "Internal server error"}), 500

# sends stored favorited pdfs to website
@app.route("/api/get-favorites")
def api_get_favorites():
    try:
        favorites = get_favorites()
        favorites_list = [{"link_url": fav[0], "favorited_at": fav[1]} for fav in favorites]
        return jsonify({
            "status": "ok",
            "favorites": favorites_list
        })
    except Exception:
        return jsonify({"error": "Failed to get favorites"}), 500

# checks if database tables exist
def ensure_tables():
    try:
        cnx = pymysql.connect(**config)
        cursor = cnx.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                link_url VARCHAR(2083) NOT NULL,
                favorited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_link (link_url)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_clicks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                link_url VARCHAR(2083) NOT NULL,
                click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cnx.commit()
        cursor.close()
        cnx.close()
    except Exception:
        pass

ensure_tables()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))