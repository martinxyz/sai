import gtk, gobject, pango, math, string
from gtk import gdk

class TextWidget(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)

        self.connect("expose-event", self.expose_cb)
        self.connect("button-press-event", self.button_press_cb)
        self.connect("button-release-event", self.button_release_cb)
        self.connect("motion-notify-event", self.motion_cb)
	self.set_events(gtk.gdk.EXPOSURE_MASK |
                        gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK
                        )
        self.set_size_request(600, 400)
        self.text = ''
        self.word_button_callbacks = []
        self.word_motion_callbacks = []
        self.word_motion_old = None

    def set_text(self, text):
        self.text = unicode(text).encode('utf8')
        self.queue_draw()

    def expose_cb(self, widget, event):
        cr = self.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        cr.clip()
        self.draw(cr, *self.window.get_size())

    def word_at(self, x, y):
        txt = self.text
        x, y = int(x), int(y) # avoid warning
        i, d = self.layout.xy_to_index(x*pango.SCALE, y*pango.SCALE) 
        # i is the byte-index of the utf8 encoded string
        #print i, d,
        if i > 0 and i < len(txt):
            def wordpart(c):
                # hack to accept utf8 alphas (can't work with real
                # unicode here, because we get the position index of
                # the utf8-encoded string)
                return c.isalpha() or c.isdigit() or ord(c) > 127
            if not wordpart(txt[i]):
                return None
            left = i
            while left > -1 and wordpart(txt[left]):
                left -= 1
            right = i
            while right < len(txt)-1 and wordpart(txt[right]):
                right += 1
            return txt[left+1:right].decode('utf8')
        else:
            return None
        

    def motion_cb(self, widget, event):
        word = self.word_at(event.x, event.y)
        if word == self.word_motion_old: return
        self.word_motion_old = word
        for f in self.word_motion_callbacks:
            f(word)

    def button_press_cb(self, widget, event):
        word = self.word_at(event.x, event.y)
        for f in self.word_button_callbacks:
            f(word, event)

    def button_release_cb(self, widget, event):
        pass
        #print 'release'
        
    def draw(self, cr, width, height):
        # Fill the background with gray
        cr.set_source_rgb(0.7, 0.7, 0.7)
        #cr.rectangle(0, 10, width, height)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        cr.set_source_rgb(0.0, 0.0, 0.2)
        # Center coordinates on the middle of the region we are drawing
        cr.translate(0, 0)
        layout = cr.create_layout()
        #width, height = layout.get_size()
        layout.set_width(width*pango.SCALE)

        attr = pango.AttrList()
        #attr.insert(pango.AttrBackground(0x5555, 0x5555, 0xffff, 5, 7))

        layout.set_text(self.text)
        layout.set_attributes(attr)
        cr.show_layout(layout)
        #cr.restore()
        self.layout = layout

