from flask import Flask, request, jsonify
import requests
import json
import re
import base64
from urllib.parse import parse_qs, urlparse
import logging

# Suppress console output
logging.getLogger().setLevel(logging.CRITICAL)

app = Flask(__name__)

def sanitize_filename(filename):
    """Remove invalid characters and query parameters from filename, ensuring extension."""
    filename = filename.split('?')[0]
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = re.sub(r'_+', '_', filename)
    filename = filename.strip('_')
    if not filename.lower().endswith(('.mp4', '.mp3')):
        filename += '.mp4'
    return filename

@app.route('/dl', methods=['GET'])
def download_tiktok_links():
    tiktok_url = request.args.get('url')
    
    if not tiktok_url or not tiktok_url.startswith("https://www.tiktok.com/"):
        return jsonify({"error": "Invalid or missing TikTok URL"}), 400
    
    # API endpoint
    api_url = "https://tikdownloader.io/api/ajaxSearch"
    
    # Headers to mimic browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://tikdownloader.io/",
        "Origin": "https://tikdownloader.io"
    }
    
    # Payload
    payload = {
        "q": tiktok_url,
        "lang": "en"
    }
    
    try:
        # Send POST request
        response = requests.post(api_url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        if data.get("status") != "ok":
            return jsonify({"error": "API returned invalid status"}), 500
        
        # Extract download links from response data
        html_content = data.get("data", "")
        if not html_content:
            return jsonify({"error": "No data found in API response"}), 500
        
        # Extract only snapcdn.app links to avoid 403 errors
        download_links = []
        filenames = []
        
        # Regex to match snapcdn.app URLs
        links = re.findall(r'href="(https://dl\.snapcdn\.app/get\?token=[^"]+)"', html_content)
        for link in links:
            download_links.append(link)
            # Extract filename from token
            parsed_url = urlparse(link)
            query_params = parse_qs(parsed_url.query)
            token = query_params.get('token', [None])[0]
            if token:
                try:
                    payload_part = token.split('.')[1]
                    payload_part += '=' * (-len(payload_part) % 4)
                    decoded = json.loads(base64.b64decode(payload_part).decode('utf-8'))
                    filename = decoded.get('filename', '')
                    if filename:
                        filenames.append(sanitize_filename(filename))
                    else:
                        filenames.append(sanitize_filename(f"TikTok_{tiktok_url.split('/')[-1]}"))
                except Exception:
                    filenames.append(sanitize_filename(f"TikTok_{tiktok_url.split('/')[-1]}"))
            else:
                filenames.append(sanitize_filename(f"TikTok_{tiktok_url.split('/')[-1]}"))
        
        if not download_links:
            return jsonify({"error": "No downloadable links found"}), 404
        
        # Prepare JSON response
        result = [
            {"url": link, "filename": filename}
            for link, filename in zip(download_links, filenames)
        ]
        
        return jsonify({"links": result})
        
    except requests.Timeout:
        return jsonify({"error": "Request timed out"}), 504
    except requests.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
