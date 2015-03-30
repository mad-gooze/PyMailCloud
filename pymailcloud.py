#!/usr/bin/python

import requests
import urlparse
import re

__version__ = "0.1"

class PyMailCloud:

    def __init__(self, login, password):

        self.Mpop = None
        self.token = None

        self.login = login
        self.password = password

        self.user_agent = "PyMailCloud/(" + __version__ + ")"

        self.__recreate_tokens()

    def __recreate_tokens(self):
        response = requests.post("http://auth.mail.ru/cgi-bin/auth",
            headers={
                "User-Agent": self.user_agent
            },
            data={
                "page": "http://cloud.mail.ru/",
                "Login": self.login,
                "Password": self.password
            }
        )


        # success?
        if response.status_code == requests.codes.ok and response.history:

            parsed = urlparse.urlparse(response.url).query
            params = urlparse.parse_qs(parsed)

            if "fail" in params:
                raise Exception("Login or password is incorrect")
            else:
                cookies_response = response.history[0]

                token = None
                # parse response html to get token
                result = re.search("\"(token)\"\:\s\"[\w]+\"", response.text)
                if result:
                    token_str = result.group()
                    result = re.findall("\"(.*?)\"", token_str)
                    if len(result) == 2:
                        token = str(result[1])
                if token and "Mpop" in cookies_response.cookies and "t" in cookies_response.cookies:
                    self.Mpop = cookies_response.cookies["Mpop"]
                    self.token = token

        else:
            raise Exception("Failed to connect")

    def get_folder_contents(self, folder):
        response = requests.get("https://cloud.mail.ru/api/v2/folder",
            params={
                "home": folder,
                "token": self.token
            },
            headers={
                "User-Agent": self.user_agent
            },
            cookies={
                "Mpop": self.Mpop
            }
        )

        if response.status_code == 200:
            # ok!
            return response.json()
        elif response.status_code == 403:
            # tokens seem to expire
            self.__recreate_tokens()
            return self.get_folder_contents(folder)
        elif response.status_code == 404:
            raise Exception("Folder not found")
        else:
            # wtf?
            raise Exception("Unknown error " + str(response.status_code) + ": " + response.text)

    def get_public_link(self, filename):

        response = requests.post("https://cloud.mail.ru/api/v2/file/publish",
            headers={
                "User-Agent": self.user_agent,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
            cookies={
                "Mpop": self.Mpop
            },
            data={
                "home": filename,
                "token": self.token
            }
        )

        if response.status_code == 200:
            # ok!
            return "https://cloud.mail.ru/public/" + response.json()["body"]
        elif response.status_code == 403:
            # tokens seem to expire
            self.__recreate_tokens()
            return self.get_public_link(filename)
        elif response.status_code == 404:
            raise Exception("File not found")
        elif response.status_code == 507:
            raise Exception("Public links number exceeded")
        else:
            # wtf?
            raise Exception("Unknown error " + str(response.status_code) + ": " + response.text)

    def remove_public_link(self, weblink):

        remove_from_start = [
            "https://cloud.mail.ru/public/",
            "http://cloud.mail.ru/public/",
            "cloud.mail.ru/public/"
        ]
        for s in remove_from_start:
            if weblink.startswith(s):
                weblink = weblink[len(s):]
                break

        response = requests.post("https://cloud.mail.ru/api/v2/file/unpublish",
            headers={
                "User-Agent": self.user_agent,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
            cookies={
                "Mpop": self.Mpop
            },
            data={
                "weblink": weblink,
                "token": self.token
            }
        )
        if response.status_code == 200:
            pass
        elif response.status_code == 404:
            raise Exception("File not found")
        else:
            # wtf?
            raise Exception("Unknown error " + str(response.status_code) + ": " + response.text)

    def download_file(self):
        raise Exception("Not implemented")
    def upload_file(self):
        raise Exception("Not implemented")