# -*- coding: utf-8 -*-

from pymailcloud import PyMailCloud

mail_cloud = PyMailCloud("test-cloud-api@mail.ru", "test-cloud-api123") # do not change the password please :)
print mail_cloud.get_public_link(u"/Берег.jpg")
#mail_cloud.remove_public_link(u"da94b3dafdc3/Берег.jpg")