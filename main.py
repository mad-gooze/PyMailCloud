# -*- coding: utf-8 -*-
import json

from PyMailCloud import PyMailCloud
from PyMailCloud import PyMailCloudError

try:
    mail_cloud = PyMailCloud("test-cloud-api@mail.ru", "test-cloud-api123") # do not change the password please :)
    #print (mail_cloud.get_folder_contents("/zr.ru/1_10/docs-000.txt"))

    #print(mail_cloud.get_folder_contents('/'))
    #print(mail_cloud.get_subfolders('/'))
    mail_cloud.download_folder_content('/MyFolder2')

    #publicLink = mail_cloud.get_public_link(u"/Берег.jpg")
    #print (publicLink)
    #try:
    #    mail_cloud.remove_public_link(publicLink)
    #    print('Link deleted successfully')
    #except PyMailCloudError as e:
    #    print(e)
    #mail_cloud.download_files(['/zr.ru/1_10/docs-000.txt', '/zr.ru/1_10/urls.txt'])
except PyMailCloudError.AuthError as e:
    print (e)
