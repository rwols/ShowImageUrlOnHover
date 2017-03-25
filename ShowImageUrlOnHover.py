import sublime
import sublime_plugin
import urllib.parse
import urllib.request
import os
import tempfile

def dequote(s):
    if (s[0] == s[-1]) and s.startswith(("'", '"')):
        return s[1:-1]
    return s

class ShowImageUrlOnHover(sublime_plugin.ViewEventListener):

    def on_hover(self, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT:
            return
        region = self.view.extract_scope(point)
        url = self.view.substr(region)
        url = dequote(url)
        parsed_url = urllib.parse.urlparse(url)
        root, ext = os.path.splitext(url)
        ext = ext.lower()
        if ext not in ('.gif', '.png', '.jpg', '.jpeg'):
            return
        # For some reason, png files from the web are not displayed.
        if parsed_url.scheme == 'https' or ext == '.png':
            temppath = os.path.join(tempfile.mkdtemp(), os.path.basename(url))
            try:
                temppath, headers = urllib.request.urlretrieve(url, temppath)
            except Exception as e:
                print(str(e))
                return
            self.temppath = temppath
            self.show_popup('file://' + temppath, point)
        elif parsed_url.scheme in ('http', 'file', 'res', 'data'):
            self.temppath = None
            self.show_popup(url, point)

    def show_popup(self, src, point):
        content = '<html><body><img src="{}"></body></html>'.format(src)
        width, height = self.view.viewport_extent()
        self.view.show_popup(
                content, 
                sublime.HIDE_ON_MOUSE_MOVE_AWAY, 
                point, # location
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



