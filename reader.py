#!/usr/bin/env python
# encoding: utf8
import gtk, sys, os, random
gdk = gtk.gdk

import textwidget, selector

class Application: # singleton
    def __init__(self):
        self.mainWindow = MainWindow(self)
        self.mainWindow.show_all()
        gtk.accel_map_load('accelmap.conf')
    def quit(self):
        gtk.accel_map_save('accelmap.conf')
        gtk.main_quit()


class MainWindow(gtk.Window):
    def __init__(self, app):
        gtk.Window.__init__(self)
        self.app = app
        def delete_event_cb(window, event): self.app.quit()
        self.connect('delete-event', delete_event_cb)

        vbox = gtk.VBox()
        self.add(vbox)

        self.create_ui()
        vbox.pack_start(self.ui.get_widget('/Menubar'), expand=False)

        self.statusbar1 = sb1 = gtk.Statusbar()
        vbox.pack_start(sb1, expand=False)

        p = gtk.HPaned()
        vbox.pack_start(p)

        w = self.textwidget = textwidget.TextWidget()
        #vbox.pack_start(w, padding=5)
        p.add1(w)

        w = self.textwidget2 = textwidget.TextWidget()
        #vbox.pack_start(w, padding=5)
        p.add2(w)

        self.statusbar2 = sb2 = gtk.Statusbar()
        vbox.pack_start(sb2, expand=False)

        self.textwidget.word_motion_callbacks.append(self.word_motion_cb)
        self.textwidget.word_button_callbacks.append(self.word_button_cb)

        self.selector = selector.Selector()
        self.update()

        self.wordAtMouse = ''

    def word_motion_cb(self, word):
        if word is None: word = ''
        self.wordAtMouse = word
        self.statusbar2.push(1, word)

    def word_button_cb(self, word, event):
        if word is None: return
        if event.button == 1:
            self.selector.markKeyword(word, +1)
            self.update()
        elif event.button == 3:
            menu = self.ui.get_widget('/WordContextPopup')
            menu.popup(None, None, None, event.button, event.time, None)

    def mark_keyword_cb(self, action):
        s = action.get_name()
        if s.endswith('Inc'):
            self.selector.markKeyword(self.wordAtMouse, +1)
        else:
            self.selector.markKeyword(self.wordAtMouse, -1000)
        self.update()

    def rate_cb(self, action):
        w = self.wordAtMouse
        if not w: return
        rating = int(action.get_name()[-1]) - 3
        #print repr(w), 'rate', rating
        self.selector.rateWord(w, rating)

    def update(self):
        if self.selector.chunk:
            keywords = ', '.join(self.selector.getKeywords())
            text = self.selector.chunk.text
            text2 = self.selector.report
        else:
            keywords = '<no article selected>'
            text = u''
            text2 = ''
        self.statusbar1.push(1, keywords)
        self.textwidget.set_text(text) 
        self.textwidget2.set_text(text2)

    def create_ui(self):
        ag = gtk.ActionGroup('WindowActions')
        # FIXME: this xml menu only creates unneeded information duplication, I think.
        ui_string = """<ui>
          <menubar name='Menubar'>
            <menu action='NavigateMenu'>
              <menuitem action='Next'/>
              <menuitem action='Random'/>
              <menuitem action='Prev'/>
              <separator/>
              <menuitem action='Browser'/>
              <separator/>
              <menuitem action='Quit'/>
            </menu>
            <menu action='WordMenu'>
              <menuitem action='Rate1'/>
              <menuitem action='Rate2'/>
              <menuitem action='Rate3'/>
              <menuitem action='Rate4'/>
              <menuitem action='Rate5'/>
              <separator/>
              <menuitem action='KeywordInc'/>
              <menuitem action='KeywordDec'/>
              <menuitem action='Relate'/>
            </menu>
          </menubar>
          <popup name='WordContextPopup'>
              <menuitem action='Rate4'/>
              <menuitem action='Rate2'/>
              <menuitem action='Rate5'/>
              <menuitem action='Rate1'/>
              <menuitem action='Rate3'/>
              <separator/>
              <menuitem action='KeywordDec'/>
              <menuitem action='Relate'/>
          </popup>
        </ui>
        """
        actions = [
            ('NavigateMenu',     None, 'Navigate'),
            ('Next',        None, 'Next', 'n', None, self.next_cb),
            ('Random',        None, 'Random', 'r', None, self.random_cb),
            ('Prev',        None, 'Prev', 'p', None, self.prev_cb),
            ('Browser',        None, 'Browser', 'b', None, self.browser_cb),
            ('Quit',        None, 'Quit', 'Escape', None, self.quit_cb),
            ('WordMenu',    None, 'Word'),
            ('Rate1',      None, '-2 Spam',        '1', None, self.rate_cb),
            ('Rate2',      None, '-1 Boring',      '2', None, self.rate_cb),
            ('Rate3',      None, ' 0 Neutral',     '3', None, self.rate_cb),
            ('Rate4',      None, '+1 Interesting', '4', None, self.rate_cb),
            ('Rate5',      None, '+2 Important',   '5', None, self.rate_cb),
            ('KeywordInc',  None, 'Mark as Keyword',    None, None, self.mark_keyword_cb),
            ('KeywordDec',  None, 'Unmark as Keyword',  None, None, self.mark_keyword_cb),
            ('Relate',      None, 'Relate, Categorize or Replace', 'l', None, None),
            ]
        ag.add_actions(actions)
        self.ui = gtk.UIManager()
        self.ui.insert_action_group(ag, 0)
        self.ui.add_ui_from_string(ui_string)
        self.app.accel_group = self.ui.get_accel_group()
        self.add_accel_group(self.app.accel_group)

    def next_cb(self, action):
        self.selector.next()
        self.update()

    def random_cb(self, action):
        self.selector.nextRandom()
        self.update()

    def prev_cb(self, action):
        self.selector.prev()
        self.update()

    def quit_cb(self, action):
        self.app.quit()

    def browser_cb(self, action):
        url = self.selector.getLink(logging=True)
        print url
        os.system('iceweasel "%s" &' % url)

def main():
    #gtksettings = gtk.settings_get_default()
    #gtksettings.set_property('gtk-can-change-accels', True)

    app = Application()

    #gtk.accel_map_load('accelmap.conf')

    gtksettings = gtk.settings_get_default()
    gtksettings.set_property('gtk-can-change-accels', True)

    gtk.main()


if __name__ == '__main__':
    main()

