#!/usr/bin/python

import requests
import urlparse
import re

__version__ = "0.1"


class PyMailCloudError(Exception):
    pass

    class AuthError(Exception):

        def __init__(self, message="Login or password is incorrect"):
            super(PyMailCloudError.AuthError, self).__init__(message)

    class NetworkError(Exception):
        def __init__(self, message="Connection failed"):
            super(PyMailCloudError.NetworkError, self).__init__(message)

    class NotFoundError(Exception):
        def __init__(self, message="File not found"):
            super(PyMailCloudError.NotFoundError, self).__init__(message)

    class PublicLinksExceededError(Exception):
        def __init__(self, message="Public links number exceeded"):
            super(PyMailCloudError.PublicLinksExceededError, self).__init__(message)

    class UnknownError(Exception):
        def __init__(self, message="WTF is going on?"):
            super(PyMailCloudError.UnknownError, self).__init__(message)

    class NotImplementedError(Exception):
        def __init__(self, message="The developer wants to sleep"):
            super(PyMailCloudError.NotImplementedError, self).__init__(message)


class PyMailCloud:

    def __init__(self, login, password):

        self.mpop = None
        self.token = None

        self.login = login
        self.password = password

        self.user_agent = "PyMailCloud/({})".format(__version__)

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
                raise PyMailCloudError.AuthError()
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
                    # save cookies for later use
                    self.mpop = cookies_response.cookies["Mpop"]
                    self.token = token

        else:
            raise PyMailCloudError.NetworkError()

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
                "Mpop": self.mpop
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
            raise PyMailCloudError.NotFoundError("Folder not found")
        else:
            # wtf?
            raise PyMailCloudError.UnknownError(str(response.status_code) + ": " + response.text)

    def get_public_link(self, filename):

        response = requests.post("https://cloud.mail.ru/api/v2/file/publish",
            headers={
                "User-Agent": self.user_agent,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
            cookies={
                "Mpop": self.mpop
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
            raise PyMailCloudError.NotFoundError("File not found")
        elif response.status_code == 507:
            raise PyMailCloudError.PublicLinksExceededError()
        else:
            # wtf?
            raise PyMailCloudError.UnknownError("{0}: {1}".format(response.status_code, response.text))

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
                "Mpop": self.mpop
            },
            data={
                "weblink": weblink,
                "token": self.token
            }
        )
        if response.status_code == 200:
            pass
        elif response.status_code == 404:
            raise PyMailCloudError.NotFoundError("File not found")
        else:
            # wtf?
            raise PyMailCloudError.UnknownError("{0}: {1}".format(response.status_code, response.text))

    def download_file(self):
        raise PyMailCloudError.NotImplementedError()

    def upload_file(self):
        raise PyMailCloudError.NotImplementedError()