# -*- coding: utf-8 -*-

from pymailcloud import PyMailCloud

mail_cloud = PyMailCloud("test-cloud-api@mail.ru", "test-cloud-api123")

print mail_cloud.get_public_link(u"/Берег.jpg")