import tornado
import argparse
import mimetypes

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

    args = parser.parse_args()

    if args.config:
        with open(args.config) as f:
            exec(compile(f.read(), args.config, 'exec'), globals())

    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
