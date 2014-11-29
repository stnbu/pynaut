# -*- coding: utf-8 -*-
from pynaut import Container
import urwid
import os
import logging

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
log_file_path = os.path.join('/tmp/.urwid_devel.log')
fh = logging.FileHandler(log_file_path)
file_formatter = logging.Formatter('%(asctime)s %(name)-12s(%(lineno)s): %(levelname)-8s %(message)s')
fh.setFormatter(file_formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


class PynautTreeWidget(urwid.TreeWidget):
    unexpanded_icon = urwid.AttrMap(urwid.TreeWidget.unexpanded_icon,
        'dirmark')
    expanded_icon = urwid.AttrMap(urwid.TreeWidget.expanded_icon,
        'dirmark')

    def __init__(self, node):
        self.__super.__init__(node)
        self._w = urwid.AttrWrap(self._w, None)
        self.flagged = False
        self.update_w()
        self.expanded = False

    def selectable(self):
        return True

    def keypress(self, size, key):
        """allow subclasses to intercept keystrokes"""
        key = self.__super.keypress(size, key)
        if key:
            key = self.unhandled_keys(size, key)
        return key

    def unhandled_keys(self, size, key):
        """
        Override this method to intercept keystrokes in subclasses.
        Default behavior: Toggle flagged on space, ignore other keys.
        """
        if key == " ":
            self.flagged = not self.flagged
            self.update_w()
        else:
            return key

    def update_w(self):
        """Update the attributes of self.widget based on self.flagged.
        """
        if self.flagged:
            self._w.attr = 'flagged'
            self._w.focus_attr = 'flagged focus'
        else:
            self._w.attr = 'body'
            self._w.focus_attr = 'focus'

    def get_display_text(self):
        return self.get_node().get_value()['summary']

class ContainerNode(urwid.ParentNode):

    def __init__(self, *args, **kwargs):
        self.container_object = args[0]
        urwid.ParentNode.__init__(self, *args, **kwargs)

    def load_widget(self):
        return PynautTreeWidget(self)

    def load_child_keys(self):
        return range(len(self.container_object.children))

    def load_child_node(self, key):
        childdata = self.container_object.children[key]
        childclass = ContainerNode
        return childclass(childdata,
                          parent=self,
                          key=key,
                          depth=self.get_depth()+1)

class ContainerTreeListBox(urwid.TreeListBox):

    def keypress(self, size, key):
        if key == 'right':
            return key
        key = self.__super.keypress(size, key)
        return self.unhandled_input(size, key)

    _container_detail_listbox = None

    def update_container_detail_listbox(self, node):
        if self._container_detail_listbox is None:
            logger.warn('_container_detail_listbox still not updated.')
            return

        container = node.container_object

        body = [urwid.Text('--- [' + container.metadata.name + '] ---'), urwid.Divider()]
        metadata = [
            ('id()', container.metadata.id),
            ('type', container.metadata.type),
        ]
        for name, value in metadata:
            text = urwid.Text('{0}:   {1}'.format(name, value))
            body.append(urwid.AttrMap(text, None, focus_map='reversed'))
        self._container_detail_listbox.original_widget = urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def __getattribute__(self, name):
        return urwid.TreeListBox.__getattribute__(self, name)

    def change_focus(self, *args, **kwargs):
        node = args[1]
        self.update_container_detail_listbox(node)
        return urwid.TreeListBox.change_focus(self, *args, **kwargs)

class PynautTreeBrowser:
    palette = [
        ('body', 'black', 'light gray'),
        ('focus', 'light gray', 'dark blue', 'standout'),
        ('head', 'yellow', 'black', 'standout'),
        ('foot', 'light gray', 'black'),
        ('key', 'light cyan', 'black','underline'),
        ('title', 'white', 'black', 'bold'),
        ('flag', 'dark gray', 'light gray'),
        ('error', 'dark red', 'light gray'),
        ]
    footer_text = [
        ('title', 'Pynaut Data Browser'), '    ',
        ('key', 'UP'), ',', ('key', 'DOWN'), ',',
        ('key', 'PAGE UP'), ',', ('key', 'PAGE DOWN'),
        '  ',
        ('key', '+'), ',',
        ('key', '-'), '  ',
        ('key', 'LEFT'), '  ',
        ('key', 'HOME'), '  ',
        ('key', 'END'), '  ',
        ('key', 'Q'),
        ]

    def __init__(self, data=None):

        rh_menu_title = u'Pynaut Python Object Browser'
        rh_menu_items = []

        self.topnode = ContainerNode(data)
        self.listbox = ContainerTreeListBox(urwid.TreeWalker(self.topnode))
        self.listbox.offset_rows = 1

        container_detail_listbox = self.get_container_detail(rh_menu_title, rh_menu_items)
        self.infobox = urwid.Padding(container_detail_listbox, left=20, right=20)
        self.listbox._container_detail_listbox = self.infobox

        self.columns = urwid.Columns([self.listbox, self.infobox])

        self.columns.set_focus_column(0)

        view = urwid.AttrWrap(self.columns, 'body')
        self.view = urwid.Frame(view) # for showing messages


    def get_container_detail(self, title, items):
        body = [urwid.Text(title), urwid.Divider()]
        for c in items:
            button = urwid.Button(c)
            body.append(urwid.AttrMap(button, None, focus_map='reversed'))
        return urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def main(self):
        global loop
        self.loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.unhandled_input)
        loop = self.loop
        self.loop.run()

    def unhandled_input(self, k):
        if k in ('q','Q'):
            raise urwid.ExitMainLoop()


def main(python_object=None):
    if python_object is None:
        python_object = os
    root = Container(python_object)
    PynautTreeBrowser(root).main()

browse = main
