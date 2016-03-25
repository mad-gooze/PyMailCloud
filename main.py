# -*- coding: utf-8 -*-

from PyMailCloud import PyMailCloud
from PyMailCloud import PyMailCloudError

try:
    mail_cloud = PyMailCloud("test-cloud-api@mail.ru", "test-cloud-api123") # do not change the password please :)
    print (mail_cloud.get_folder_contents("/"))
    publicLink = mail_cloud.get_public_link(u"/Берег.jpg")
    print (publicLink)
    try:
        mail_cloud.remove_public_link(publicLink)
        print('Link deleted successfully')
    except PyMailCloudError as e:
        print(e)
except PyMailCloudError.AuthError as e:
    print (e)
#mail_cloud.remove_public_link(u"da94b3dafdc3/Берег.jpg")
