from flask import Flask, request, render_template, jsonify, session
import os
import requests
import pymysql
import pymysql.cursors
from google.cloud import vision

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "super_secret_dev_key_123")

API_KEY = os.environ.get("API_KEY")
CX = os.environ.get("CX")

def get_db_config():
    db_config = {
        'database': os.environ.get('DB_NAME', 'pdf_finder'),
        'user': os.environ.get('DB_USER', 'appuser'),
        'password': os.environ.get('DB_PASSWORD', 'Ajiefw9340*'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    if os.environ.get('K_SERVICE'):
        db_config['unix_socket'] = '/cloudsql/cs446-finalproject-group-7:us-central1:pdf-finder-db-1'
    else:
        db_config['host'] = os.environ.get('DB_HOST', '34.66.54.180')
        
    return db_config

config = get_db_config()


def get_current_user_key():
    return session.get('user_key', 'public')


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


def get_favorites():
    user_key = get_current_user_key()
    try:
        cnx = pymysql.connect(**config)
        cursor = cnx.cursor()
        cursor.execute("""
            SELECT link_url, favorited_at 
            FROM pdf_favorites 
            WHERE user_key = %s
            ORDER BY favorited_at DESC
        """, (user_key,))
        favorites = cursor.fetchall()
        cursor.close()
        cnx.close()

        formatted_favorites = []
        for fav in favorites:
            link_url = fav['link_url']
            favorited_at = fav['favorited_at']
            formatted_time = favorited_at.strftime('%Y-%m-%d %H:%M') if favorited_at else 'Recently'
            formatted_favorites.append((link_url, formatted_time))

        return formatted_favorites
    except Exception as e:
        print(f"Error fetching favorites for key {user_key}: {e}")
        return []

def store_favorite(link_url):
    user_key = get_current_user_key()
    try:
        cnx = pymysql.connect(**config)
        cursor = cnx.cursor()
        cursor.execute("""
            INSERT IGNORE INTO pdf_favorites (link_url, user_key) 
            VALUES (%s, %s)
        """, (link_url, user_key))
        cnx.commit()
        cursor.close()
        cnx.close()
    except Exception as e:
        raise e

def remove_favorite(link_url):
    user_key = get_current_user_key()
    try:
        cnx = pymysql.connect(**config)
        cursor = cnx.cursor()
        cursor.execute("""
            DELETE FROM pdf_favorites 
            WHERE link_url = %s AND user_key = %s
        """, (link_url, user_key))
        cnx.commit()
        cursor.close()
        cnx.close()
    except Exception as e:
        raise e

def store_click(link_url):
    try:
        cnx = pymysql.connect(**config)
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO pdf_clicks (link_url) VALUES (%s)", (link_url,))
        cnx.commit()
        cursor.close()
        cnx.close()
        return True
    except Exception as e:
        print(f"Error storing click: {e}")
        return False



@app.route("/", methods=["GET", "POST"])
def home():
    pdfs = []
    extracted_text = ""
    query = ""
    error_message = None
    results_found = True

    current_key = get_current_user_key()
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
                        if not pdfs:
                            results_found = False
                else:
                    results_found = True

        except Exception as e:
            error_message = f"Internal server error: {e}"
            results_found = True

    if error_message:
        return render_template("error.html", error_message=error_message)

    return render_template("index.html", pdfs=pdfs, query=query, favorites=favorites, user_key=current_key, results_found=results_found)

@app.route("/api/set-key", methods=["POST"])
def set_user_key():
    data = request.get_json()
    new_key = data.get("key", "").strip()
    
    if new_key:
        session['user_key'] = new_key
    else:
        session['user_key'] = 'public'
        
    return jsonify({"status": "ok", "key": session['user_key']})

@app.route("/api/click", methods=["POST"])
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

@app.route("/api/favorite", methods=["POST"])
def api_favorite():
    try:
        data = request.get_json()
        link = data.get("link_url")
        action = data.get("action", "add")
        
        if not link:
            return jsonify({"error": "Missing link_url"}), 400

        if action == "remove":
            remove_favorite(link)
        else:
            store_favorite(link)

        return jsonify({
            "status": "ok",
            "favorited": link,
            "action": action
        })

    except Exception as e:
        error_msg = f"Database operation failed: {str(e)}"
        print(f"FATAL FAVORITE ERROR: {error_msg}")
        return jsonify({"error": error_msg}), 500

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



def ensure_tables():
    try:
        cnx = pymysql.connect(**config)
        cursor = cnx.cursor()

        # 1. Clicks Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_clicks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                link_url VARCHAR(2083) NOT NULL,
                click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_key VARCHAR(255) DEFAULT 'public',
                link_url VARCHAR(2083) NOT NULL,
                favorited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user_link (user_key, link_url)
            )
        """)
        
        cnx.commit()
        cursor.close()
        cnx.close()
    except Exception as e:
        print(f"DB Initialization Error: {e}")
ensure_tables()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
