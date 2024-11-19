import base64
import json
import secrets
import string
from datetime import datetime, timedelta

import requests


class Authenticator:
    def loadJson(path=None, account=None):
        jsonFile = json.load(open(path, "r"))
        return jsonFile[account]

    def __init__(self, account):
        self.account = account
        self.path = "/home/csabimvp/code/rolling-stones-top-500/assets/credentials.json"
        self.today = datetime.now()
        self.keys = Authenticator.loadJson(path=self.path, account=self.account)

    def getClientId(self):
        return self.keys["CLIENT_ID"]

    def getClientSecret(self):
        return self.keys["CLIENT_SECRET"]

    def getCode(self):
        return self.keys["CODE"]

    def getAccessToken(self):
        return self.keys["ACCESS_TOKEN"]

    def getExpiryDate(self):
        return self.keys["EXPIRY_DATE"]

    def getGrantType(self):
        return self.keys["GRANT_TYPE"]

    def getRefreshToken(self):
        return self.keys["REFRESH_TOKEN"]

    def getRefreshTokenUrl(self):
        return self.keys["TOKEN_URL"]

    def getHeaders(self):
        headers = {
            "Authorization": f"Bearer {self.getAccessToken()}",
            "Content-Type": "application/json",
        }
        return headers

    def requestAccessCode(self):
        def generate_state(lenght=50):
            characters = string.ascii_letters + string.digits
            result_str = "".join(secrets.choice(characters) for i in range(lenght))
            return result_str

        state = generate_state()
        client_id = self.getClientId()
        redirect_uri = "https://csabakeller.com/api/webscrapers/authenticate/"
        scope = (
            "user-top-read"
            + "%20"
            + "user-read-recently-played"
            + "%20"
            + "user-read-email"
        )
        url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}&state={state}"
        return print(url)

    def requestAccessToken(self):
        url = "https://accounts.spotify.com/api/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.getClientId(),
            "client_secret": self.getClientSecret(),
            "redirect_uri": "https://csabakeller.com/api/webscrapers/authenticate/",
            "code": self.getCode(),
        }
        r = requests.post(url=url, data=payload).json()
        print(r)
        expires_in = r["expires_in"]
        new_expiry_date = self.today + timedelta(seconds=expires_in)

        # Updating keys
        self.keys["ACCESS_TOKEN"] = r["access_token"]
        self.keys["EXPIRY_DATE"] = new_expiry_date.strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.keys["SCOPE"] = r["scope"]
            self.keys["REFRESH_TOKEN"] = r["refresh_token"]
        except:
            pass
        # Saving to database.
        self.saveJson()

    def isTokenExpired(self) -> bool:
        expiryDate = datetime.strptime(self.keys["EXPIRY_DATE"], "%Y-%m-%d %H:%M:%S")
        if expiryDate < self.today:
            return True

    def saveJson(self):
        with open(self.path, "r+") as jsonFile:
            data = json.load(jsonFile)
            data[self.account] = self.keys
            jsonFile.seek(0)
            json.dump(data, jsonFile, indent=4, sort_keys=True)
            jsonFile.truncate()

    def refreshToken(self):
        isTokenExpired = self.isTokenExpired()
        if isTokenExpired:
            # Admin for API call.
            auth_client = self.getClientId() + ":" + self.getClientSecret()
            auth_encode = "Basic " + base64.b64encode(auth_client.encode()).decode()
            payload = {
                "grant_type": self.getGrantType(),
                "refresh_token": self.getRefreshToken(),
                # "client_id": self.getClientId(),
                # "code": self.getCode(),
            }
            headers = {"Authorization": auth_encode}
            url = self.getRefreshTokenUrl()

            # Refreshing Token
            r = requests.post(url=url, headers=headers, data=payload)
            if r.status_code == 200:
                response = r.json()
                expires_in = response["expires_in"]
                new_expiry_date = self.today + timedelta(seconds=expires_in)

                # Updating keys
                self.keys["ACCESS_TOKEN"] = response["access_token"]
                self.keys["EXPIRY_DATE"] = new_expiry_date.strftime("%Y-%m-%d %H:%M:%S")
                try:
                    self.keys["SCOPE"] = response["scope"]
                    self.keys["REFRESH_TOKEN"] = response["refresh_token"]
                except:
                    pass
                # Saving to database.
                self.saveJson()
                return print("Access token refreshed.")
            else:
                print(r)
