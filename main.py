# -*- coding: utf-8 -*-

from PyMailCloud import PyMailCloud
from PyMailCloud import PyMailCloudError

try:
    mail_cloud = PyMailCloud("test-cloud-api@mail.ru", "test-cloud-api123") # do not change the password please :)
    print mail_cloud.get_public_link(u"/Берег.jpg")
except PyMailCloudError.AuthError as e:
    print e
#mail_cloud.remove_public_link(u"da94b3dafdc3/Берег.jpg")