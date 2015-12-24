import tornado
import argparse
import mimetypes
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import json
import os

from nbconvert.exporters import HTMLExporter

# default config
base_url = '/'


@tornado.gen.coroutine
def path_for_url_segment(url_segment):
    return url_segment


class MainHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, filename):
        exporter = HTMLExporter()
        path = yield path_for_url_segment(filename)
        try:
            with open(path) as f:
                if path.endswith('.ipynb'):
                    html, res = exporter.from_file(f)
                    self.write(html)
                else:
                    return self.handle_static_file(path)
        except FileNotFoundError:
            raise tornado.web.HTTPError(404)

    def guess_mimetype(self, path):
        # Stolen from StaticFileHandler
        mime_type, encoding = mimetypes.guess_type(path)
        if encoding == "gzip":
            # per RFC 6713, use the appropriate type for a gzip compressed file
            return "application/gzip"
        elif encoding is not None:
            # As of 2015-07-21 there is no bzip2 encoding defined at
            # http://www.iana.org/assignments/media-types/media-types.xhtml
            # So for that (and any other encoding), use octet-stream.
            return "application/octet-stream"
        elif mime_type is not None:
            return mime_type
        else:
            # if mime_type not detected, use application/octet-stream
            return "application/octet-stream"

    @tornado.gen.coroutine
    def handle_static_file(self, path):
        # Stolen from StaticFileHandler
        self.set_header('Content-Type', self.guess_mimetype(path))
        content = tornado.web.StaticFileHandler.get_content(path)
        if isinstance(content, bytes):
            content = [content]
        for chunk in content:
            try:
                self.write(chunk)
                yield self.flush()
            except tornado.iostream.StreamClosedError:
                return


def register_proxy(proxy_url, path_prefix, target, auth_token):
    client = AsyncHTTPClient()
    url = proxy_url + path_prefix
    body = {'target': target}
    req = HTTPRequest(
        url,
        method='POST',
        headers={'Authorization': 'token {}'.format(auth_token)},
        body=json.dumps(body),
    )

    return client.fetch(req)


def make_app():
    return tornado.web.Application([
        (r"{}(.*)".format(base_url), MainHandler),
    ], autoreload=True)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        help='Path to config file',
    )
    parser.add_argument(
        '--bind-ip',
        help='IP on which to listen for requests',
        default='127.0.0.1',
    )
    parser.add_argument(
        '--bind-port',
        help='Port on which to listen for requests',
        default=8889
    )

    parser.add_argument(
        '--proxy-api-url',
        help='Full URL of the CHP REST API',
    )
    parser.add_argument(
        '--proxy-target-ip',
        help='IP for the proxy proxy requests back to',
    )
    args = parser.parse_args()

    if args.config:
        with open(args.config) as f:
            exec(compile(f.read(), args.config, 'exec'), globals())

    app = make_app()

    app.listen(args.bind_port, address=args.bind_ip)
    if args.proxy_api_url:
        if args.proxy_target_ip:
            target_ip = args.proxy_target_ip
        else:
            target_ip = args.bind_ip
        auth_token = os.environ['CONFIGPROXY_AUTH_TOKEN']
        tornado.ioloop.IOLoop.current().run_sync(lambda: register_proxy(
            args.proxy_api_url,
            base_url,
            'http://{}:{}'.format(target_ip, args.bind_port),
            auth_token,
        ))
    tornado.ioloop.IOLoop.current().start()
