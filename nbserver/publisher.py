import tornado
import mimetypes
import os

from traitlets.config import Configurable
from traitlets import Unicode


class Publisher(Configurable):
    @tornado.gen.coroutine
    def content_for_url_segment(self, url_segment):
        """
        Return a tuple of (file_like_obj, mimetype) to be served for this url segment
        """
        raise NotImplementedError('Override in subclass')


class NaiveFilesystemPublisher(Publisher):
    base_path = Unicode(
        os.getcwd(),
        config=True,
        help='The base path where user homedirs are stored',
    )

    def guess_mimetype(self, path):
        # Stolen from StaticFileHandler
        # shortcircuit .ipynb files
        # FIXME: Integrate this shortcircuit into the mimetypes module
        if path.endswith('.ipynb'):
            return 'application/x-ipynb+json'
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
    def path_for_url_segment(self, url_segment):
        return os.path.join(self.base_path, url_segment)

    @tornado.gen.coroutine
    def content_for_url_segment(self, url_segment):
        path = yield self.path_for_url_segment(url_segment)
        mimetype = self.guess_mimetype(path)
        return (open(path), mimetype)
