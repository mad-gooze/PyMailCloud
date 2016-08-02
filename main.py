#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import gnupg
import os

from PyMailCloud import PyMailCloud
from PyMailCloud import PyMailCloudError

try:

    gpg = gnupg.GPG(homedir='/home/vasy/.gnupg/')
#    with open('/home/vasy/PyMailCloud/README.md', 'rb') as f:
#         kwargs = dict (symmetric=True,
#                        passphrase='test',
#                        encrypt=False,
#                        armor=False,
#                        output='/home/vasy/PyMailCloud/README.md.gpg')
#         gpg.encrypt (f, None, **kwargs)

    mail_cloud = PyMailCloud("test@mail.ru", "test") # do not change the password please :)

    for (dir, _, files) in os.walk("/srv/nfs/foto"):
        for f in files:
            path = os.path.join(dir, f)
            if os.path.exists(path):
                print path, ' - ', os.path.getmtime(path)
                try:
                    print (mail_cloud.get_folder_contents(path+'.gpg'))
                except PyMailCloudError.NotFoundError as e:
                    print path, ' - ', e
                    with open(path, 'rb') as fe:
                        kwargs = dict (symmetric=True,
                                       passphrase='test',
                                       encrypt=False,
                                       armor=False,
                                       output='/tmp/'+os.path.basename(path)+'.gpg')
                        gpg.encrypt (fe, None, **kwargs)
                    print(mail_cloud.upload_files([{'filename': '/tmp/'+os.path.basename(path)+'.gpg', 'path': dir+'/'}]))
                    os.remove('/tmp/'+os.path.basename(path)+'.gpg')

    #print (mail_cloud.get_folder_contents("/zr.ru/1_10/docs-000.txt"))

    #print(mail_cloud.get_folder_contents('/'))
    #print(mail_cloud.get_subfolders('/'))
    #mail_cloud.download_folder_content('/MyFolder2')
#    print(mail_cloud.upload_files([{'filename': "/home/vasy/PyMailCloud/README.md.gpg", 'path': '/'}]))
    #mail_cloud.delet_files(([{'filename': "d2.pcap"}]))
#    os.remove('/home/vasy/PyMailCloud/README.md.gpg')

    #'''
    #{
   #"body": "overquota",
   #"email": "test-cloud-api@mail.ru",
   #"status": 507,
   #'''
    #mail_cloud.upload_files(['C:\Fallout 4\Data\Fallout4 - Voices.ba2'])

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
