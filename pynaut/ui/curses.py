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


class DialogFrame(urwid.Frame):
    def keypress(self, size, key):
        if key == 'tab':
            if self.focus_part == 'body':
                self.set_focus('footer')
                return None
            elif self.focus_part == 'footer':
                self.set_focus('body')
                return None
            else:
                self.__super.keypress(size, key)
        return self.__super.keypress(size, key)

class EditDialog(urwid.WidgetWrap):

    __metaclass__ = urwid.signals.MetaSignals
    signals = ['commit_text']

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
        ('border','black','white'),
        ('shadow','white','black'),
        ('selectable','black', 'dark cyan'),
        ('focustext','light gray','dark blue'),
        ('button normal','light gray', 'dark blue', 'standout'),
        ('button select','white',      'dark green'),
        ]
    parent = None
    def __init__(self, width, height, header_text=None, editor_label=None, loop=None):
        width = int(width)
        if width <= 0:
            width = ('relative', 80)
        height = int(height)
        if height <= 0:
            height = ('relative', 80)

        self.edit = urwid.Edit()
        self.body = urwid.ListBox(urwid.SimpleListWalker([
            urwid.AttrWrap(urwid.Text(editor_label), None, 'reveal focus'),
            urwid.AttrWrap(self.edit, None, 'reveal focus'),
        ]))
        self.frame = DialogFrame(self.body, focus_part = 'body')

        if header_text is not None:
            self.frame.header = urwid.Pile( [urwid.Text(header_text),
                urwid.Divider(u'\u2550')] )
        w = self.frame

        # pad area around listbox
        w = urwid.Padding(w, ('fixed left',2), ('fixed right',2))
        w = urwid.Filler(w, ('fixed top',1), ('fixed bottom',1))
        w = urwid.AttrWrap(w, 'body')

        w = urwid.LineBox(w)

        # "shadow" effect
        w = urwid.Columns( [w,('fixed', 1, urwid.AttrWrap(
            urwid.Filler(urwid.Text(('border',' ')), "top")
            ,'shadow'))])
        w = urwid.Frame( w, footer =
            urwid.AttrWrap(urwid.Text(('border',' ')),'shadow'))
        if loop is None:
            # this dialog is the main window
            # create outermost border area
            w = urwid.Padding(w, 'center', width )
            w = urwid.Filler(w, 'middle', height )
            w = urwid.AttrWrap( w, 'border' )
        else:
            # this dialog is a child window
            # overlay it over the parent window
            self.loop = loop
            self.parent = self.loop.widget
            w = urwid.Overlay(w, self.parent, 'center', width+2, 'middle', height+2)
        self.view = w

        urwid.WidgetWrap.__init__(self, self.view)

        self._add_buttons([("OK", 0, self._ok), ("Cancel", 1, self._cancel)])

    def _add_buttons(self, buttons):
        l = []
        for name, exitcode, callback in buttons:
            b = urwid.Button(name, callback)
            b.exitcode = exitcode
            b = urwid.AttrWrap( b, 'button normal','button select' )
            l.append( b )
        self.buttons = urwid.GridFlow(l, 10, 3, 1, 'center')
        self.frame.footer = urwid.Pile( [ urwid.Divider(u'\u2500'),
            self.buttons ], focus_item = 1)

    def _button(self, *args, **kwargs):
        self.loop.widget = self.parent

    def _ok(self, *args, **kwargs):
        urwid.emit_signal(self, 'commit_text', self.edit.get_edit_text())
        self._button(self, *args, **kwargs)

    def _cancel(self, *args, **kwargs):
        self._button(self, *args, **kwargs)

    def show(self):
        self.loop.widget = self.view

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

    def get_center_header_text(self):
        text = []
        text.append(u' ##### [ {0} ] ##### '.format(self.container_object.metadata.name))
        text.append(u'known object count: {0}'.format(self.container_object.container_cache_size))
        text = u'\n'.join(text)
        return text

    def get_container_info_widget(self):
        body = [urwid.Text('--- [' + str(self.container_object.metadata.name) + '] ---'), urwid.Divider()]
        metadata = [
            ('id()', self.container_object.metadata.id),
            ('type', self.container_object.metadata.type),
            ('doc', self.container_object.metadata.doc),
            ('file', self.container_object.metadata.file),
        ]
        for name, value in metadata:
            text = urwid.Text('{0}:   {1}'.format(name, value))
            body.append(urwid.AttrMap(text, None, focus_map='reversed'))
        return urwid.ListBox(urwid.SimpleFocusListWalker(body))

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
        self.container_detail_box = pad(self.topnode.get_container_info_widget())

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

    def find_object_by_regex(self, regex):
        pass

    def main(self):
        global loop
        self.loop = urwid.MainLoop(self.topmost, self.palette, unhandled_input=self.unhandled_input, pop_ups=True)
        loop = self.loop
        self.loop.run()

    def unhandled_input(self, k):
        if k in ('q','Q'):
            raise urwid.ExitMainLoop()
        if k in ('t', 'T'):
            d = EditDialog(40, 10, 'Find Object by Attribute Regex', 'python regex: ', self.loop)
            urwid.connect_signal(d, 'commit_text', self.find_object_by_regex)
            d.show()

    def on_listbox_node_change(self, *args, **kwargs):
        node = args[0]

        list_box = node.get_container_info_widget()
        self.container_detail_box.original_widget = list_box
        text = node.get_center_header_text()
        self.header_center.set_text(text)

def main(python_object=None):
    if python_object is None:
        python_object = globals()
    root = Container(python_object)
    PynautTreeBrowser(root).main()

browse = main
