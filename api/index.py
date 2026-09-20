from flask import Flask, request, jsonify
from datetime import datetime, timezone
import requests

app = Flask(__name__)

PLAYFAB_TITLE_ID = "496EC"
PLAYFAB_SECRET_KEY = "41O3MOR8OUCMGD6PQPARSGSBFZSWX9FIEKT6P8T48859DPEMJT"
META_API_KEY = "yourmetaapi/OC|"
AUTH_WEBHOOK = "https://discord.com/api/webhooks/1551037523570991128/p0N72GymQ-I7w6UZqAA-XMxRBrkkDtljwSJSOOM_m-D4G5UkvVhqlzrDzmhRR3VzAmt6"

PLAYFAB_BASE_URL = f"https://{PLAYFAB_TITLE_ID}.playfabapi.com"


def get_json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def get_playfab_headers():
    return {
        "Content-Type": "application/json",
        "X-SecretKey": PLAYFAB_SECRET_KEY
    }


def is_valid_playfab_request():
    title_id = request.headers.get("X-PlayFabTitleId")
    if not title_id:
        return True
    return title_id == PLAYFAB_TITLE_ID


def send_auth_log(playfab_id, oculus_id, custom_id, platform):
    if not AUTH_WEBHOOK or AUTH_WEBHOOK == "YOUR_DISCORD_WEBHOOK_URL":
        return

    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

    if ip_address and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()

    payload = {
        "embeds": [{
            "title": "Player Authenticated",
            "description": "A player successfully authenticated.",
            "fields": [
                {
                    "name": "PlayFab ID",
                    "value": f"`{playfab_id or 'Unknown'}`",
                    "inline": False
                },
                {
                    "name": "Oculus ID",
                    "value": f"`{oculus_id or 'Unknown'}`",
                    "inline": False
                },
                {
                    "name": "Oculus Custom ID",
                    "value": f"`{custom_id or 'Unknown'}`",
                    "inline": False
                },
                {
                    "name": "IP Address",
                    "value": f"`{ip_address or 'Unknown'}`",
                    "inline": False
                },
                {
                    "name": "Platform",
                    "value": f"`{platform or 'Unknown'}`",
                    "inline": True
                },
                {
                    "name": "Time",
                    "value": f"`{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`",
                    "inline": True
                }
            ]
        }]
    }

    try:
        requests.post(
            AUTH_WEBHOOK,
            json=payload,
            timeout=5
        )
    except requests.RequestException:
        pass


@app.route("/", methods=["GET"])
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>turbo-tag-v3-backend</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {
                box-sizing: border-box;
            }

            html, body {
                margin: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: #000;
            }

            body {
                background-image: url("https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=2400&q=90");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
            }

            .overlay {
                position: absolute;
                inset: 0;
                background: rgba(0, 0, 0, 0.25);
            }

            .content {
                position: relative;
                z-index: 1;
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
                color: white;
                font-family: Arial, sans-serif;
                text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8);
            }

            h1 {
                font-size: 42px;
                margin: 0 0 10px;
            }

            p {
                font-size: 18px;
                margin: 0;
            }
        </style>
    </head>
    <body>
        <div class="overlay"></div>
        <div class="content">
            <h1>turbo-tag-v3-backend</h1>
            <p>if you see this it is working</p>
        </div>
    </body>
    </html>
    """


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "status": "online"
    })


@app.route("/api/TD", methods=["POST"])
def titled_data():
    return jsonify({
        "MOTD": " <color=red>WELCOME TO CRIMSON TAG </color>\n<color=green>𝙵𝚛𝚘𝚜𝚝𝚣𝚣 IS THE OWNER AND UNH4PPY IS THE DEV</color>\n<color=red>discord.gg/KCWWBvZh5</color>\n<color=green>CREDITS:MEEP FOR BACKEND<color>
  "
    })


@app.route("/api/PlayFabAuthentication", methods=["POST"])
def playfab_authentication():
    data = get_json()

    oculus_id = data.get("OculusId")
    nonce = data.get("Nonce", "Null")
    platform = data.get("Platform", "Null")

    if not oculus_id:
        return jsonify({
            "Message": "Missing OculusId"
        }), 400

    custom_id = f"OCULUS{oculus_id}"

    try:
        login_req = requests.post(
            f"{PLAYFAB_BASE_URL}/Server/LoginWithServerCustomId",
            headers=get_playfab_headers(),
            json={
                "ServerCustomId": custom_id,
                "CreateAccount": True
            },
            timeout=10
        )

        playfab_result = login_req.json()

        if login_req.status_code != 200:
            if playfab_result.get("errorCode") == 1002:
                details = playfab_result.get("errorDetails", {})

                ban_reason = next(
                    iter(details.keys()),
                    "Banned"
                )

                ban_time = details.get(
                    ban_reason,
                    ["Indefinite"]
                )[0]

                return jsonify({
                    "BanMessage": ban_reason,
                    "BanExpirationTime": ban_time
                }), 403

            return jsonify({
                "Message": "Login failed",
                "Error": playfab_result.get(
                    "errorMessage",
                    "Unknown PlayFab error"
                )
            }), 403

        result = playfab_result.get("data", {})

        session_ticket = result.get("SessionTicket")
        playfab_id = result.get("PlayFabId")
        entity = result.get("EntityToken", {})

        entity_token = entity.get("EntityToken")
        entity_id = entity.get("Entity", {}).get("Id")
        entity_type = entity.get("Entity", {}).get("Type")

        send_auth_log(
            playfab_id,
            oculus_id,
            custom_id,
            platform
        )

        return jsonify({
            "PlayFabId": playfab_id,
            "SessionTicket": session_ticket,
            "EntityToken": entity_token,
            "EntityId": entity_id,
            "EntityType": entity_type,
            "Nonce": nonce,
            "OculusId": oculus_id,
            "Platform": platform
        }), 200

    except requests.RequestException:
        return jsonify({
            "Message": "Could not connect to PlayFab"
        }), 502


@app.route("/api/CachePlayFabId", methods=["POST"])
def cache_playfab_id():
    if not is_valid_playfab_request():
        return jsonify({
            "success": False,
            "error": "Invalid PlayFab title ID"
        }), 401

    data = get_json()

    playfab_id = (
        data.get("PlayFabId")
        or data.get("playFabId")
        or data.get("UserId")
    )

    cache_id = (
        data.get("CacheId")
        or data.get("cacheId")
    )

    if not playfab_id:
        return jsonify({
            "success": False,
            "error": "Missing PlayFab ID"
        }), 400

    if not cache_id:
        return jsonify({
            "success": False,
            "error": "Missing cache ID"
        }), 400

    return jsonify({
        "success": True,
        "PlayFabId": playfab_id,
        "CacheId": cache_id,
        "message": "Cache ID received"
    })


@app.route("/api/Photon", methods=["POST"])
def photon():
    data = get_json()

    return jsonify({
        "ResultCode": 1,
        "StatusCode": 200,
        "Message": "authed with photon",
        "Result": 0,
        "UserId": data.get("UserId"),
        "AppId": data.get("AppId"),
        "AppVersion": data.get("AppVersion"),
        "Ticket": data.get("Ticket"),
        "Token": data.get("Token"),
        "Nonce": data.get("Nonce"),
        "Platform": data.get("Platform"),
        "Username": data.get("Username"),
        "PlayerRoomCount": data.get("PlayerRoomCount"),
        "GorillaTagger": data.get("GorillaTagger"),
        "CosmeticAuthentication": data.get("CosmeticAuthenticationV2"),
        "CosmeticsInRoom": data.get("CosmeticsInRoom"),
        "UpdatePlayerCosmetics": data.get("UpdatePlayerCosmetics"),
        "DLCOwnerShip": data.get("DLCOwnerShipV2"),
        "Currency": data.get("GorillaCorpCurrencyV1"),
        "RoomJoined": data.get("RoomJoined"),
        "VirtualStump": data.get("VirtualStump"),
        "DeadMonke": data.get("DeadMonke"),
        "GhostCounter": data.get("GhostCounter"),
        "BroadcastRoom": data.get("BroadcastMyRoomV2"),
        "TaggedClient": data.get("TaggedClient"),
        "TaggedDistance": data.get("TaggedDistance"),
        "RPCS": data.get("RPCS")
    })

@app.route("/api/MetaCheck", methods=["POST"])
def meta_check():
    provided_key = request.headers.get("X-Meta-API-Key")

    if not META_API_KEY or META_API_KEY == "YOUR_META_API_KEY":
        return jsonify({
            "success": False,
            "error": "Meta API key has not been configured"
        }), 503

    if not provided_key or provided_key != META_API_KEY:
        return jsonify({
            "success": False,
            "error": "Invalid Meta API key"
        }), 401

    return jsonify({
        "success": True,
        "authenticated": True
    })

@app.route("/api/SetName", methods=["POST"])
def set_name():
    data = get_json()

    session_ticket = data.get("SessionTicket")
    name = data.get("DisplayName") or data.get("Name")

    if not session_ticket:
        return jsonify({
            "success": False,
            "error": "Missing SessionTicket"
        }), 400

    if not name:
        return jsonify({
            "success": False,
            "error": "Missing name"
        }), 400

    if len(name) > 25:
        return jsonify({
            "success": False,
            "error": "Name is too long"
        }), 400

    try:
        response = requests.post(
            f"{PLAYFAB_BASE_URL}/Client/UpdateUserTitleDisplayName",
            headers={
                "Content-Type": "application/json",
                "X-Authorization": session_ticket
            },
            json={
                "DisplayName": name
            },
            timeout=10
        )

        result = response.json()

        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": result.get(
                    "errorMessage",
                    "Could not change name"
                )
            }), response.status_code

        return jsonify({
            "success": True,
            "DisplayName": result.get("data", {}).get(
                "DisplayName",
                name
            )
        }), 200

    except requests.RequestException:
        return jsonify({
            "success": False,
            "error": "Could not connect to PlayFab"
        }), 502

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": "Method not allowed"
    }), 405


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
