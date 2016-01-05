import tornado
from tornado import gen
import json
import os
from nbserver import FileSystemPublisher


class PAWSPublisher(FileSystemPublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_uids = {}

    @gen.coroutine
    def uid_for_user(self, user):
        url = 'https://meta.wikimedia.org/w/api.php?' + \
              'action=query&meta=globaluserinfo' + \
              '&format=json&formatversion=2' + \
              '&guiuser={}'.format(user)
        client = tornado.httpclient.AsyncHTTPClient()

        resp = yield client.fetch(url)

        parsed = json.loads(resp.body.decode('utf-8'))
        if 'missing' in parsed['query']['globaluserinfo']:
            return None
        return parsed['query']['globaluserinfo']['id']

    @gen.coroutine
    def path_for_url_segment(self, url_segment):
        """
        Takes a URL segment and returns a full filesystem path

        Example:
            input: YuviPanda/Something.ipynb
            output: 43/public/Something.ipynb
        """
        splits = url_segment.split('/')

        # We want to deny any path where any component starts with a .
        # FIXME: Check and verify if usernames can start with a .
        for component in splits:
            if component.startswith('.'):
                raise FileNotFoundError()
        username = splits[0]
        path = '/'.join(splits[1:])
        if username in self.cached_uids:
            uid = self.cached_uids[username]
        else:
            uid = yield self.uid_for_user(username)
            if uid is None:
                raise tornado.web.HTTPError(404)
            self.cached_uids[username] = uid

        return os.path.join(self.base_path, str(uid), 'public', path)
