#!/usr/bin/python
import os
import re
import errno
import requests
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

from tqdm import tqdm

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
    class FileSizeError(Exception):
        def __init__(self, message="The file is bigger than 2 GB"):
            super(PyMailCloudError.FileSizeError, self).__init__(message)


class PyMailCloud:
    def __init__(self, login, password):

        self.user_agent = "PyMailCloud/({})".format(__version__)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        self.login = login
        self.password = password
        self.downloadSource = None
        self.uploadTarget = None
        self.__recreate_token()

    def __get_download_source(self):
        dispatcher = self.session.get('https://cloud.mail.ru/api/v2/dispatcher',
                                      params={
                                          "token": self.token
                                      }, )
        if dispatcher.status_code is not 200:
            raise PyMailCloudError.NetworkError
        # print(json.loads(dispatcher.content.decode("utf-8")))
        self.downloadSource = json.loads(dispatcher.content.decode("utf-8"))['body']['get'][0]['url']
        self.uploadTarget = json.loads(dispatcher.content.decode("utf-8"))['body']['upload'][0]['url']
        print('Acquired CDN Node')

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
            self.__get_download_source()
        else:
            raise PyMailCloudError.NetworkError()

    def get_subfolders(self, folder):
        folderlist = []
        foldercount = 0
        foldercountlast = 0
        run = True
        rootFolderContents = json.loads(self.get_folder_contents(folder))
        print('Listing directory {}'.format(folder))
        folderlist.append(folder)
        if rootFolderContents['body']['count']['folders'] == 0:
            run = False
        while run:
            for e in rootFolderContents['body']['list']:
                if 'count' in e and e['count']['folders'] == 0 or rootFolderContents['body']['count']['folders'] == 0:
                    run = False
                if e['type'] == 'folder':
                    list = self.get_subfolders(e['home'])
                    for f in list:
                        folderlist.append(f)
                    foldercount += 1
                if foldercount == foldercountlast:
                    run = False
                else:
                    foldercountlast = foldercount
        return folderlist

    def get_folder_contents(self, folder):
        response = self.session.get("https://cloud.mail.ru/api/v2/folder",
                                    params={
                                        "home": folder,
                                        "token": self.token
                                    },
                                    )

        if response.status_code == 200:
            # ok!
            return json.dumps(response.json(), sort_keys=True, indent=3, ensure_ascii=False)
        elif response.status_code == 403:
            # tokens seem to expire
            print("Got HTTP 403 on listing folder contents, retrying...")
            self.__recreate_token()
            return self.get_folder_contents(folder)
        elif response.status_code == (400 or 404):
            raise PyMailCloudError.NotFoundError("File or folder not found")
        else:
            # wtf?
            raise PyMailCloudError.UnknownError(str(response.status_code) + ": " + response.text)

    def download_folder_content(self, folder):
        folderlist = self.get_subfolders(folder)
        filedownloadlist = []
        for f in folderlist:
            metadata = json.loads(self.get_folder_contents(f))
            if metadata['body']['count']['files'] == 0:
                break
            # metadata = list((filemeta for filemeta in metadataList['body']['list'] if filemeta['home'] == file))[0]

            for file in list((file for file in metadata['body']['list'] if file['type'] == 'file')):
                filedownloadlist.append(file['home'])
            self.download_files(filedownloadlist)

    def get_public_link(self, filename):

        response = self.session.post("https://cloud.mail.ru/api/v2/file/publish",
                                     headers={
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

    def download_files(self, filenamelist):
        for file in filenamelist:
            response = self.session.get(self.downloadSource[:-1] + file,
                                        stream=True)
            if response.status_code == 404:
                raise PyMailCloudError.NotFoundError("File not found")

            print("Getting metadata for file {}".format(file))
            metadataList = json.loads(self.get_folder_contents(file))
            metadata = list((filemeta for filemeta in metadataList['body']['list'] if filemeta['home'] == file))[0]

            print('Downloading "{}"'.format(file))
            # remove leading slash
            file = re.sub(r"^\/", './', file)

            if not os.path.exists(os.path.dirname(file)):
                try:
                    os.makedirs(os.path.dirname(file))
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
            with open(file, "wb") as handle:
                for data in tqdm(response.iter_content(chunk_size=1024), unit='KB', total=int(metadata['size'] / 1024)):
                    handle.write(data)
            print('')



    def upload_callback(self, monitor, progress):
        #print('Length: {}, read: {}'.format(monitor.len, monitor.bytes_read))
        progress.total = monitor.len
        progress.update(8192)
        pass

    def upload_files(self, fileslist):
        path = ''
        progress = tqdm(unit='B')
        for file in fileslist:
            progress.desc = file['filename']
            try:
                f = open(file['filename'], 'rb')
            except FileNotFoundError:
                print("File not found: {}".format(file['filename']))
                break
            files = {'file': f}

            if 'path' not in file: path = '/'
            else: path = file['path']
            destination = path + os.path.basename(file['filename'])
            if os.path.getsize(file['filename']) > 1024 * 1024 * 1024 * 2:
                raise PyMailCloudError.FileSizeError
            monitor = MultipartEncoderMonitor.from_fields(
                fields={'file': ('filename', f, 'application/octet-stream')},
                callback=lambda monitor: self.upload_callback(monitor, progress))
            upload_response = self.session.post(self.uploadTarget, data=monitor,
                              headers={'Content-Type': monitor.content_type})
            if upload_response.status_code is not 200:
                raise PyMailCloudError.NetworkError

            hash, filesize = upload_response.content.decode("utf-8").split(';')[0], upload_response.content.decode("utf-8").split(';')[1][:-2]
            response = self.session.post("https://cloud.mail.ru/api/v2/file/add",  # "http://httpbin.org/post",
                                         data={
                                             "token": self.token,
                                             "home": destination,
                                             "conflict": 'rename',
                                             "hash": hash,
                                             "size": filesize,
                                         })
            return json.dumps(response.json(), sort_keys=True, indent=3, ensure_ascii=False)

    def delete_files(self, fileslist):
        path = ''
        progress = tqdm(unit='B')
        for file in fileslist:
            response = self.session.post("https://cloud.mail.ru/api/v2/file/remove",  # "http://httpbin.org/post",
                                         data={
                                             "token": self.token,
                                             "home": file['filename'],
                                             "hash": hash,
                                         })
            return json.dumps(response.json(), sort_keys=True, indent=3, ensure_ascii=False)
