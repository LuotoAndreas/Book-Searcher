from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import re
import time

app = Flask(__name__)

#cache = {}
#CACHE_EXPIRATION = 60 * 5  # cache for 5 minutes (300 seconds)

@app.route('/')
def home():
    return render_template("index.html")

def get_description(key):
    url = f"https://openlibrary.org{key}.json"
    response = requests.get(url)
    if response.status_code == 200:
        description = response.json().get("description")
        if isinstance(description, dict):
            desc_text = description.get("value", "")
        elif isinstance(description, str):
            desc_text = description
        else:
            desc_text = ""
        return clean_description(desc_text)
    return "No description available"

def clean_description(desc):
    if not desc:
        return "No description available"
    
    # Remove markdown links: [text](url) -> text
    desc = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', desc)
    
    # Remove markdown bold/italic markers (e.g., **text**, *text*)
    desc = re.sub(r'(\*\*|\*)', '', desc)
    
    # Split description into lines
    lines = desc.splitlines()
    
    # Filter out lines starting with certain patterns
    filtered_lines = [
        line for line in lines
        if not (line.startswith('(') or line.startswith('http') or line.startswith('/http') or line.startswith('Contains'))
    ]
    
    # Join back filtered lines and strip extra whitespace
    cleaned_desc = '\n'.join(filtered_lines).strip()
    
    # Remove multiple newlines if any
    cleaned_desc = re.sub(r'\n+', '\n', cleaned_desc)
    
    return cleaned_desc if cleaned_desc else "No description available"




@app.route('/search', methods=['GET'])
def search_books():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    # Check cache first
    #cached = cache.get(query)
    #if cached:
    #    timestamp, data = cached
    #    if time.time() - timestamp < CACHE_EXPIRATION:
    #        return jsonify(data)

    url = f"https://openlibrary.org/search.json?q={query}"
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch data"}), 500

    data = response.json()
    books = []

    # Only take first 10 results for performance
    for book in data.get("docs", [])[:5]:
        work_key = book.get("key")
        description = get_description(work_key) if work_key else "No description available"

        books.append({
            "title": book.get("title"),
            "author": ", ".join(book.get("author_name", [])),
            "year": book.get("first_publish_year"),
            "description": description,
            "cover": f"https://covers.openlibrary.org/b/olid/{book.get('cover_edition_key')}-M.jpg"
                     if book.get('cover_edition_key') else None
        })

    # Store in cache
    #cache[query] = (time.time(), books)
    return jsonify(books)


if __name__ == "__main__":
    app.run(debug=True)
