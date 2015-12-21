from tornado import gen
from tornado.httpclient import AsyncHTTPClient
import json
import os


BASE_PATH = '.'

base_url = '/paws/public/'


@gen.coroutine
def uid_for_user(user):
    url = 'https://meta.wikimedia.org/w/api.php?' + \
          'action=query&meta=globaluserinfo' + \
          '&format=json&formatversion=2' + \
          '&guiuser={}'.format(user)
    client = AsyncHTTPClient()

    resp = yield client.fetch(url)

    parsed = json.loads(resp.body.decode('utf-8'))
    return parsed['query']['globaluserinfo']['id']


cached_uids = {}


@gen.coroutine
def path_for_url_segment(url):
    """
    Takes a URL segment and returns a full filesystem path

    Example:
        input: YuviPanda/Something.ipynb
        output: 43/public/Something.ipynb
    """
    splits = url.split('/')
    username = splits[0]
    path = '/'.join(splits[1:])
    if username in cached_uids:
        uid = cached_uids[username]
    else:
        uid = yield uid_for_user(username)
        cached_uids[username] = uid

    return os.path.join(BASE_PATH, str(uid), 'public', path)
