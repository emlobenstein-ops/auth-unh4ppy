import requests
import random
import json
from flask import Flask, jsonify, request


class GameInfo:

    def __init__(self):
        titleider: str = "496EC"
        secretkey: str = "41O3MOR8OUCMGD6PQPARSGSBFZSWX9FIEKT6P8T48859DPEMJT"
        self.ApiKey: str = "OC|1273571995844746|834042b3ed1bbe0299cc9c7339cc99a8"

    def GetAuthHeaders(self) -> dict:
        return {
            "content-type": "application/json",
            "X-SecretKey": secretkey
        }

def GetTitle(self) -> str:
        return titleider


settings = GameInfo()
app: Flask = Flask(__name__)
playfabCache: dict = {}
muteCache: dict = {}

titleider = ""
secretkey = ""
settings.ApiKey = ""


def ReturnFunctionJson(data, funcname, funcparam={}):
    rjson = data["FunctionParameter"]
    userId: str = rjson.get("CallerEntityProfile").get("Lineage").get(
        "TitlePlayerAccountId")

    req = requests.post(
        url=f"https://{titleider}.playfabapi.com/Server/ExecuteCloudScript",
        json={
            "PlayFabId": userId,
            "FunctionName": funcname,
            "FunctionParameter": funcparam
        },
        headers=settings.GetAuthHeaders())

    if req.status_code == 200:
        return jsonify(
            req.json().get("data").get("FunctionResult")), req.status_code
    else:
        return jsonify({}), req.status_code


def GetIsNonceValid(nonce: str, oculusId: str):
    req = requests.post(
        url=f'https://graph.oculus.com/user_nonce_validate?nonce=' + nonce +
        '&user_id=' + oculusId + '&access_token=' + settings.ApiKey,
        headers={"content-type": "application/json"})
    return req.json().get("is_valid")


@app.route("/", methods=["POST", "GET"])
def main():
    return "your not supposed to be here .."


# Replace https://auth-prod.gtag-cf.com/api/PlayFabAuthentication with this endpoint
@app.route("/api/playfabauthenticate", methods=["POST", "GET"])
def playfabauthentication():
    rjson = request.get_json()

    if rjson.get("CustomId") is None:
        return jsonify({
            "Message": "Missing CustomId parameter",
            "Error": "BadRequest-NoCustomId"
        })
    if rjson.get("Nonce") is None:
        return jsonify({
            "Message": "Missing Nonce parameter",
            "Error": "BadRequest-NoNonce"
        })
    if rjson.get("AppId") is None:
        return jsonify({
            "Message": "Missing AppId parameter",
            "Error": "BadRequest-NoAppId"
        })
    if rjson.get("Platform") is None:
        return jsonify({
            "Message": "Missing Platform parameter",
            "Error": "BadRequest-NoPlatform"
        })
    if rjson.get("OculusId") is None:
        return jsonify({
            "Message": "Missing OculusId parameter",
            "Error": "BadRequest-NoOculusId"
        })

    if rjson.get("AppId") != titleider:
        return jsonify({
            "Message": "Request sent for the wrong App ID",
            "Error": "BadRequest-AppIdMismatch"
        })
    if not rjson.get("CustomId").startswith("OC") and not rjson.get(
            "CustomId").startswith("PI"):
        return jsonify({
            "Message": "Bad request",
            "Error": "BadRequest-No OC or PI Prefix"
        })

    url = f"https://{titleider}.playfabapi.com/Server/LoginWithServerCustomId"
    login_request = requests.post(url=url,
                                  json={
                                      "ServerCustomId": rjson.get("CustomId"),
                                      "CreateAccount": True
                                  },
                                  headers=settings.GetAuthHeaders())

    if login_request.status_code == 200:
        data = login_request.json().get("data")
        sessionTicket = data.get("SessionTicket")
        entityToken = data.get("EntityToken").get("EntityToken")
        playFabId = data.get("PlayFabId")
        entityType = data.get("EntityToken").get("Entity").get("Type")
        entityId = data.get("EntityToken").get("Entity").get("Id")

        print(
            requests.post(
                url=f"https://{titleider}.playfabapi.com/Client/LinkCustomID",
                json={
                    "ForceLink": True,
                    "CustomId": rjson.get("CustomId")
                },
                headers=settings.GetAuthHeaders()).json())

        return jsonify({
            "PlayFabId": playFabId,
            "SessionTicket": sessionTicket,
            "EntityToken": entityToken,
            "EntityId": entityId,
            "EntityType": entityType
        })
    else:
        errorDetails = login_request.json().get('errorDetails')
        firstBan = next(iter(errorDetails))
        return jsonify({
            "BanMessage": str(firstBan),
            "BanExpirationTime": str(errorDetails[firstBan])
        })


# Replace https://auth-prod.gtag-cf.com/api/CachePlayFabId with this endpoint
@app.route("/api/cacheplayfabid", methods=["POST", "GET"])
def cacheplayfabid():
    rjson = request.get_json()

    playfabCache[rjson.get("PlayFabId")] = rjson

    return jsonify({"Message": "Success"}), 200


# Replace https://title-data.gtag-cf.com with this endpoint

@app.route("/api/TitleData", methods=["POST", "GET"])
def titledata():
    req = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/GetTitleData",
        headers=settings.GetAuthHeaders()
    )
    if req.status_code == 200:
        return jsonify(req.json().get("data").get("Data"))
    else:
        return jsonify({})




# Replace https://iap.gtag-cf.com/api/ConsumeOculusIAP with this endpoint


@app.route("/api/consumeiap", methods=["POST", "GET"])
def consumeoculusiap():
    rjson = request.get_json()

    accessToken = rjson.get("userToken")
    userId = rjson.get("userID")
    playFabId = rjson.get("playFabId")
    nonce = rjson.get("nonce")
    platform = rjson.get("platform")
    sku = rjson.get("sku")
    debugParams = rjson.get("debugParemeters")

    req = requests.post(
        url=
        f"https://graph.oculus.com/consume_entitlement?nonce={nonce}&user_id={userId}&sku={sku}&access_token="
        + settings.ApiKey,
        headers={"content-type": "application/json"})

    if bool(req.json().get("success")):
        return jsonify({"result": True})
    else:
        return jsonify({"error": True})


@app.route("/api/photon", methods=["POST"])
def photonauth():
    print(f"Received {request.method} request at /api/photon")
    getjson = request.get_json()
    Ticket = getjson.get("Ticket")
    Nonce = getjson.get("Nonce")
    Platform = getjson.get("Platform")
    UserId = getjson.get("UserId")
    nickName = getjson.get("username")
    if request.method.upper() == "GET":
        rjson = request.get_json()
        print(f"{request.method} : {rjson}")

        userId = Ticket.split('-')[0] if Ticket else None
        print(f"Extracted userId: {UserId}")

        if userId is None or len(userId) != 16:
            print("Invalid userId")
            return jsonify({
                'resultCode': 2,
                'message': 'Invalid token',
                'userId': None,
                'nickname': None
            })

        if Platform != 'Quest':
            return jsonify({
                'Error': 'Bad request',
                'Message': 'Invalid platform!'
            }), 403

        if Nonce is None:
            return jsonify({
                'Error': 'Bad request',
                'Message': 'Not Authenticated!'
            }), 304

        req = requests.post(
            url=f"https://{titleider}.playfabapi.com/Server/GetUserAccountInfo",
            json={"PlayFabId": userId},
            headers={
                "content-type": "application/json",
                "X-SecretKey": secretkey
            })

        print(f"Request to PlayFab returned status code: {req.status_code}")

        if req.status_code == 200:
            nickName = req.json().get("UserInfo",
                                      {}).get("UserAccountInfo",
                                              {}).get("Username")
            if not nickName:
                nickName = None

            print(
                f"Authenticated user {userId.lower()} with nickname: {nickName}"
            )

            return jsonify({
                'resultCode': 1,
                'message':
                f'Authenticated user {userId.lower()} title {titleider.lower()}',
                'userId': f'{userId.upper()}',
                'nickname': nickName
            })
        else:
            print("Failed to get user account info from PlayFab")
            return jsonify({
                'resultCode': 0,
                'message': "Something went wrong",
                'userId': None,
                'nickname': None
            })

    elif request.method.upper() == "POST":
        rjson = request.get_json()
        print(f"{request.method} : {rjson}")

        ticket = rjson.get("Ticket")
        userId = ticket.split('-')[0] if ticket else None
        print(f"Extracted userId: {userId}")

        if userId is None or len(userId) != 16:
            print("Invalid userId")
            return jsonify({
                'resultCode': 2,
                'message': 'Invalid token',
                'userId': None,
                'nickname': None
            })

        req = requests.post(
            url=f"https://496EC.playfabapi.com/Server/GetUserAccountInfo",
            json={"PlayFabId": userId},
            headers={
                "content-type": "application/json",
                "X-SecretKey": secretkey
            })

        print(f"Authenticated user {userId.lower()}")
        print(f"Request to PlayFab returned status code: {req.status_code}")

        if req.status_code == 200:
            nickName = req.json().get("UserInfo",
                                      {}).get("UserAccountInfo",
                                              {}).get("Username")
            if not nickName:
                nickName = None
            return jsonify({
                'resultCode': 1,
                'message':
                f'Authenticated user {userId.lower()} title {titleider.lower()}',
                'userId': f'{userId.upper()}',
                'nickname': nickName
            })
        else:
            print("Failed to get user account info from PlayFab")
            successJson = {
                'resultCode': 0,
                'message': "Something went wrong",
                'userId': None,
                'nickname': None
            }
            authPostData = {}
            for key, value in authPostData.items():
                successJson[key] = value
            print(f"Returning successJson: {successJson}")
            return jsonify(successJson)
    else:
        print(f"Invalid method: {request.method.upper()}")
        return jsonify({
            "Message":
            "Use a POST or GET Method instead of " + request.method.upper()
        })


def ReturnFunctionJson(data, funcname, funcparam={}):
    print(f"Calling function: {funcname} with parameters: {funcparam}")
    rjson = data.get("FunctionParameter", {})
    userId = rjson.get("CallerEntityProfile",
                       {}).get("Lineage", {}).get("TitlePlayerAccountId")

    print(f"UserId: {userId}")

    req = requests.post(
        url=f"https://496EC.playfabapi.com/Server/ExecuteCloudScript",
        json={
            "PlayFabId": userId,
            "FunctionName": funcname,
            "FunctionParameter": funcparam
        },
        headers={
            "content-type": "application/json",
            "X-SecretKey": secretkey
        })

    if req.status_code == 200:
        result = req.json().get("data", {}).get("FunctionResult", {})
        print(f"Function result: {result}")
        return jsonify(result), req.status_code
    else:
        print(f"Function execution failed, status code: {req.status_code}")
        return jsonify({}), req.status_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
