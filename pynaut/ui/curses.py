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

def get_container_list_box(container_instance=None):

    if container_instance is not None:
        body = [urwid.Text('--- [' + str(container_instance.metadata.name) + '] ---'), urwid.Divider()]
        metadata = [
            ('id()', container_instance.metadata.id),
            ('type', container_instance.metadata.type),
        ]
    else:
        body = [urwid.Text(''), urwid.Divider()]
        metadata = []

    for name, value in metadata:
        text = urwid.Text('{0}:   {1}'.format(name, value))
        body.append(urwid.AttrMap(text, None, focus_map='reversed'))

    return urwid.ListBox(urwid.SimpleFocusListWalker(body))

class ContainerTreeListBox(urwid.TreeListBox):

    on_listbox_node_change = None

    def change_focus(self, *args, **kwargs):
        node = args[1]
        if self.on_listbox_node_change is None:
            logger.warn('on_listbox_node_change attribute still not set.')
        else:
            self.on_listbox_node_change(node)
        return urwid.TreeListBox.change_focus(self, *args, **kwargs)

class PynautTreeBrowser:
    palette = [
        (None, 'dark red', 'light gray'),  # Make it visible
        ('body', 'black', 'light gray'),
        ('flagged', 'black', 'dark green', ('bold','underline')),
        ('focus', 'light gray', 'dark blue', 'standout'),
        ('flagged focus', 'yellow', 'dark cyan',
                ('bold','standout','underline')),
        ('head', 'yellow', 'black', 'standout'),
        ('foot', 'light gray', 'black'),
        ('key', 'light cyan', 'black','underline'),
        ('title', 'white', 'black', 'bold'),
        ('dirmark', 'black', 'dark cyan', 'bold'),
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

        def pad(w):
            return urwid.Padding(w, left=20, right=20)

        self.topnode = ContainerNode(data)
        self.container_tree_list_box = ContainerTreeListBox(urwid.TreeWalker(self.topnode))
        self.container_detail_box = pad(get_container_list_box())

        self.container_tree_list_box.on_listbox_node_change = self.on_listbox_node_change

        self.columns = urwid.Columns(
            [
                urwid.LineBox(self.container_tree_list_box),
                urwid.LineBox(self.container_detail_box)
             ])
        self.columns.set_focus_column(0)

        self.header_left = urwid.Text('this is the left header column')
        self.header_center = urwid.Text('this is the center header column')
        self.header_right = urwid.Text('this is the left header column')

        header = urwid.AttrWrap(urwid.Columns([self.header_left, self.header_center, self.header_right]), 'head')

        footer = urwid.AttrWrap(urwid.Text(self.footer_text), 'foot')
        self.topmost = urwid.Frame(urwid.AttrWrap(self.columns, 'body'), header=header, footer=footer)

    def main(self):
        global loop
        self.loop = urwid.MainLoop(self.topmost, self.palette, unhandled_input=self.unhandled_input)
        loop = self.loop
        self.loop.run()

    def unhandled_input(self, k):
        if k in ('q','Q'):
            raise urwid.ExitMainLoop()

    def on_listbox_node_change(self, *args, **kwargs):
        node = args[0]
        container_instance = node.container_object
        list_box = get_container_list_box(container_instance)
        self.container_detail_box.original_widget = list_box
        attr_name = u' ##### [ {0} ] ##### '.format(container_instance.metadata.name)
        self.header_center.set_text(attr_name)

def main(python_object=None):
    if python_object is None:
        python_object = os
    root = Container(python_object)
    PynautTreeBrowser(root).main()

browse = main
