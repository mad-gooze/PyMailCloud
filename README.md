# PyMailCloud
Unofficial python library for making API requests to [Cloud@Mail.ru](http://cloud.mail.ru/)

## Supported methods

### PyMailCloud(login, password)
Creates PyMailCloud object or raises an exception if login and password are incorrect, or internet connection is failed.

### PyMailCloud.get_folder_contents(folder)
*folder* - folder path relative to cloud home

Returns some strange internal mail.ru JSON object containing folder contents.

### PyMailCloud.get_public_link(filename)
*filename* - file path relative to cloud home

Returns full public URL of file, or rises an exception in case of error.
