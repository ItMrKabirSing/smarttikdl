from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def welcome():
    return jsonify({
        "message": "👋 Welcome to the TikTok Downloader API!",
        "usage": "Use the /dl?url=YOUR_TIKTOK_URL endpoint",
        "developer": "@ISmartCoder"
    })

@app.route('/dl', methods=['GET'])
def download_tiktok():
    tiktok_url = request.args.get('url')
    if not tiktok_url:
        return jsonify({
            "success": False,
            "error": "Missing TikTok URL parameter `url`",
            "developer": "@ISmartCoder"
        }), 400

    api_url = "https://downloader.bot/api/tiktok/info"
    payload = {"url": tiktok_url}

    try:
        response = requests.post(api_url, json=payload)
        data = response.json()

        if data.get("error"):
            return jsonify({
                "success": False,
                "error": data["error"],
                "developer": "@ISmartCoder"
            }), 500

        info = data["data"]

        return jsonify({
            "success": True,
            "developer": "@ISmartCoder",
            "creator": info.get("nick"),
            "caption": info.get("video_info"),
            "thumbnail": info.get("video_img"),
            "video_url": info.get("mp4"),
            "audio_url": info.get("mp3")
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "developer": "@ISmartCoder"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
