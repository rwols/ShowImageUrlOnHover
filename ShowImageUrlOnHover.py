import sublime
import sublime_plugin
import urllib.parse
import urllib.request
import os
import tempfile
import threading
import re

def dequote(s):
    if (s[0] == s[-1]) and s.startswith(("'", '"')):
        return s[1:-1]
    return s

"""
the web url matching regex used by markdown
http://daringfireball.net/2010/07/improved_regex_for_matching_urls
https://gist.github.com/gruber/8891611
"""
URL_REGEX = r"""(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))"""

class ShowImageUrlOnHover(sublime_plugin.ViewEventListener):

    def on_hover(self, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT:
            return
        if self.view.match_selector(point, 'comment') or self.view.match_selector(point, 'text'):
            self.url = self.extract_from_line_in_plaintext(point)
        else:
            self.url = self.extract_from_scope(point)
        if not self.url:
            return
        root, ext = os.path.splitext(self.url)
        self.ext = ext.lower()
        if self.ext not in ('.gif', '.png', '.jpg', '.jpeg'):
            return
        self.point = point
        threading.Thread(target=self.download_image).start()

    def extract_from_line_in_plaintext(self, point):
        line = self.view.substr(self.view.line(point))
        match = re.search(URL_REGEX, line)
        return match.group(0) if match else None

    def extract_from_scope(self, point):
        region = self.view.extract_scope(point)
        url = self.view.substr(region)
        return dequote(url)

    def download_image(self):
        parsed_url = urllib.parse.urlparse(self.url)
        # For some reason, png files from the web are not displayed.
        # gifs also give problems.
        if parsed_url.scheme == 'https' or self.ext == '.png' or self.ext == '.gif':
            self.temppath = os.path.join(tempfile.mkdtemp(), os.path.basename(self.url))
            try:
                self.temppath, headers = urllib.request.urlretrieve(self.url, self.temppath)
            except Exception as e:
                print(str(e))
                return
            self.show_popup('file://' + self.temppath)
        elif parsed_url.scheme in ('http', 'file', 'res', 'data'):
            self.temppath = None
            self.show_popup(self.url)

    def show_popup(self, src):
        content = '<html><body><img src="{}"></body></html>'.format(src)
        width, height = self.view.viewport_extent()
        self.view.show_popup(
                content, 
                sublime.HIDE_ON_MOUSE_MOVE_AWAY, 
                self.point, # location
                width, # max width
                height, # max height
                self.on_navigate,
                self.on_hide)

    def on_navigate(self, href):
        pass

    def on_hide(self):
        if not self.temppath:
            return
        os.remove(self.temppath)
        self.temppath = None

# These are test strings. Uncomment and hover over them to test them.
# test_large_png = 'http://bellard.org/bpg/3.png'
# test_large_jpg = 'https://upload.wikimedia.org/wikipedia/commons/8/8c/Chess_Large.JPG'
# test_large_jpeg = 'https://upload.wikimedia.org/wikipedia/commons/d/d5/Dds40-097_large.jpeg'
# test_animated_gif = 'http://netdna.webdesignerdepot.com/uploads/2013/07/icons-animation.gif'



