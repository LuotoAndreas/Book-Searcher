from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import time

app = Flask(__name__)

cache = {}
CACHE_EXPIRATION = 60 * 5  # cache for 5 minutes (300 seconds)

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/search', methods=['GET'])
def search_books():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    # Check cache first
    cached = cache.get(query)
    if cached:
        timestamp, data = cached
        if time.time() - timestamp < CACHE_EXPIRATION:
            return jsonify(data)

    # Open Library API Request
    url = f"https://openlibrary.org/search.json?q={query}"
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch data"}), 500

    data = response.json()
    books = [
        {
            "title": book.get("title"),
            "author": ", ".join(book.get("author_name", [])),
            "year": book.get("first_publish_year"),
            ""
            "cover": f"https://covers.openlibrary.org/b/olid/{book.get('cover_edition_key')}-M.jpg"
            if book.get('cover_edition_key') else None
        }
        for book in data.get("docs", [])
    ]
    # Store in cache
    cache[query] = (time.time(), books)
    return jsonify(books)

if __name__ == "__main__":
    app.run(debug=True)
