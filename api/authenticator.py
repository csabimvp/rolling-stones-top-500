import json
from datetime import datetime, timedelta

import requests


class Authenticator:
    def loadJson(path=None, account=None):
        jsonFile = json.load(open(path, "r"))
        return jsonFile[account]

    def __init__(self, account):
        self.account = account
        self.path = "/home/pi/airflow/assets/credentials.json"
        self.today = datetime.now()
        self.keys = Authenticator.loadJson(path=self.path, account=self.account)

    def getClientId(self):
        return self.keys["CLIENT_ID"]

    def getClientSecret(self):
        return self.keys["CLIENT_SECRET"]

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

    def isTokenExpired(self):
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
            payload = {
                "grant_type": self.getGrantType(),
                "client_id": self.getClientId(),
                "client_secret": self.getClientSecret(),
                "refresh_token": self.getRefreshToken(),
            }
            url = self.getRefreshTokenUrl()
            r = requests.post(url=url, data=payload).json()
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
