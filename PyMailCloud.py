#!/usr/bin/python

import requests
import json

__version__ = "0.2"


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

        self.user_agent = "PyMailCloud/({})".format(__version__)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        self.login = login
        self.password = password
        self.__recreate_token()

    def __recreate_token(self):
        loginResponse = self.session.post("https://auth.mail.ru/cgi-bin/auth",
                                     data={
                                         "page": "http://cloud.mail.ru/",
                                         "Login": self.login,
                                         "Password": self.password
                                     },
                                     )
        # success?
        if loginResponse.status_code == requests.codes.ok and loginResponse.history:
            getTokenResponse = self.session.post("https://cloud.mail.ru/api/v2/tokens/csrf")
            if getTokenResponse.status_code is not 200:
                raise PyMailCloudError.UnknownError
            self.token = json.loads(getTokenResponse.content.decode("utf-8"))['body']['token']
            print('Login successful')
        else:
            raise PyMailCloudError.NetworkError()

    def get_folder_contents(self, folder):
        response = self.session.get("https://cloud.mail.ru/api/v2/folder",
                                    params={
                                        "home": folder,
                                        "token": self.token
                                    },
                                    headers={
                                        "User-Agent": self.user_agent
                                    },

                                    )

        if response.status_code == 200:
            # ok!
            return json.dumps(response.json(), sort_keys=True, indent=4, ensure_ascii=False)
        elif response.status_code == 403:
            # tokens seem to expire
            print("Got HTTP 403 on listing folder contents, retrying...")
            self.__recreate_token()
            return self.get_folder_contents(folder)
        elif response.status_code == 404:
            raise PyMailCloudError.NotFoundError("Folder not found")
        else:
            # wtf?
            raise PyMailCloudError.UnknownError(str(response.status_code) + ": " + response.text)

    def get_public_link(self, filename):

        response = self.session.post("https://cloud.mail.ru/api/v2/file/publish",
                                     headers={
                                         "User-Agent": self.user_agent,
                                         "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
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
            self.__recreate_token()
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

        response = self.session.post("https://cloud.mail.ru/api/v2/file/unpublish",
                                     headers={
                                         "User-Agent": self.user_agent,
                                         "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
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
