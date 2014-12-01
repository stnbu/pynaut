# -*- coding: utf-8 -*-
from pynaut import Container
import urwid
import os
import re
import logging
import curses

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
log_file_path = os.path.join('/tmp/.urwid_devel.log')
fh = logging.FileHandler(log_file_path)
file_formatter = logging.Formatter('%(asctime)s %(name)-12s(%(lineno)s): %(levelname)-8s %(message)s')
fh.setFormatter(file_formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

def make_grid(rows):
    """
    rows = [
        [5, urwid.Text('fdsafsad'), urwid.Text('fdsafsad') ],
        [20, urwid.Text('fdsafsad'), urwid.Text('fdsafsad') ],
        [5, urwid.Text('fdsafsad'), urwid.Text('fdsafsad'), urwid.Text('fdsafsad') ],
    ]
    """
    def get_cell(widget, height):
        widget = urwid.Filler(widget, 'top', None, height)
        widget = urwid.BoxAdapter(widget, height)
        return widget
    placeholder = urwid.Text('')
    grid_width = len(max(rows, key=len)) - 1
    grid = []
    for row in rows:
        height = row[0]
        cells = row[1:]
        r = []
        pad = [placeholder] * (grid_width - len(cells))
        for cell in cells + pad:
            if isinstance(cell, tuple):
                cell = list(cell)
                widget = cell[-1]
                widget = get_cell(widget, height)
                cell = tuple(cell[:-1] + widget)
            else:
                cell = get_cell(cell, height)
            r.append(cell)
        r = urwid.Columns(r)
        grid.append(r)
    return urwid.ListBox(urwid.SimpleListWalker(grid))

class DialogFrame(urwid.Frame):

    def __init__(self, *args, **kwargs):
        self.escape = kwargs.pop('escape')
        urwid.Frame.__init__(self, *args, **kwargs)
    def keypress(self, size, key):
        if key == 'tab':
            if self.focus_part == 'body':
                self.set_focus('footer')
            elif self.focus_part == 'footer':
                self.set_focus('body')
        elif key in ['esc',]:
            self.escape()
        return self.__super.keypress(size, key)

class EditDialog(urwid.WidgetWrap):

    __metaclass__ = urwid.signals.MetaSignals
    signals = ['commit_text']

    parent = None
    def __init__(self, width, height, initial_text='', header_text=None, editor_label=None, loop=None):
        if loop is None:
            raise ValueError('loop is a required argument.')

        width = int(width)
        if width <= 0:
            width = ('relative', 80)
        height = int(height)
        if height <= 0:
            height = ('relative', 80)

        self.edit = urwid.Edit(initial_text)
        self.body = urwid.ListBox(urwid.SimpleListWalker([
            urwid.AttrWrap(urwid.Text(editor_label), None, 'reveal focus'),
            urwid.AttrWrap(self.edit, None, 'reveal focus'),
        ]))
        self.frame = DialogFrame(self.body, focus_part = 'body', escape=self.on_cancel)

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
        w = urwid.Frame( w, footer = urwid.AttrWrap(urwid.Text(('border',' ')),'shadow'))
        self.loop = loop
        self.parent = self.loop.widget
        w = urwid.Overlay(w, self.parent, 'center', width+2, 'middle', height+2)
        self.view = w

        self._add_buttons([("OK", 0, self.on_ok), ("Cancel", 1, self.on_cancel)])

        urwid.WidgetWrap.__init__(self, self.view)


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

    def on_ok(self, *args, **kwargs):
        urwid.emit_signal(self, 'commit_text', self.edit.get_edit_text())
        self._button(self, *args, **kwargs)

    def on_cancel(self, *args, **kwargs):
        self._button(self, *args, **kwargs)

    def show(self):
        self.loop.widget = self.view

    def keypress(self, size, key):
        if key == 'esc':
            self.loop.widget = self.parent
        elif key == '7':
            self.loop.widget = self.parent
        return self.__super.keypress(size, key)

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
        self.flagged_nodes = set()

    def selectable(self):
        return True

    def keypress(self, size, key):
        """allow subclasses to intercept keystrokes"""
        key = self.__super.keypress(size, key)
        if key:
            key = self.unhandled_keys(size, key)
        return key

    def unhandled_keys(self, size, key):
        if key == " ":
            self.flagged = not self.flagged
            self.update_w()
            container_object = self.get_node().get_value()
            if self.flagged:
                self.flagged_nodes.add(container_object)
                logger.warn('adding {0} to list of flagged_nodes for {1}'.format(repr(container_object), repr(self)))
            else:
                if container_object in self.flagged_nodes:
                    self.flagged_nodes.remove(container_object)
                    logger.warn('removing {0} from list of flagged_nodes for {1}'.format(repr(container_object), repr(self)))
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
        self.container_object.children.sort()

    def forget_children(self):
        self._child_keys = None
        self._children = {}

    def get_center_header_text(self):
        text = []
        text.append(u' ##### [ {0} ] ##### '.format(self.container_object.metadata.name))
        text.append(u'known object count: {0}'.format(self.container_object.container_cache_size))
        text = u'\n'.join(text)
        return text

    def get_container_info_widget(self):
        body = [urwid.Text('--- [' + str(self.container_object.metadata.name) + '] ---'), urwid.Divider()]
        metadata = [
            # (height, label, value)
            (1, 'id()', self.container_object.metadata.id),
            (1, 'type', self.container_object.metadata.type),
            (1, 'file', self.container_object.metadata.file),
            (1, 'is module', self.container_object.metadata.ismodule),
            (1, 'parent module', self.container_object.metadata.parent_module),
            (3, 'names in sys.modules', self.container_object.metadata.imported_names),
            (3, 'known aliases', self.container_object.metadata.known_aliases),
            (20, 'doc', self.container_object.metadata.doc),
        ]

        rows = [[h, urwid.Text(unicode(n)), urwid.Text(unicode(v))] for h, n, v in metadata]
        body = make_grid(rows)
        return body

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
        ('body', 'black', 'light gray'),
        ('dirmark', 'black', 'dark cyan', 'bold'),
        ('error', 'dark red', 'light gray'),
        ('even row', 'dark gray', 'light gray'),
        ('flag', 'dark gray', 'light gray'),
        ('flagged focus', 'yellow', 'dark cyan', ('bold','standout','underline')),
        ('flagged', 'black', 'dark green', ('bold','underline')),
        ('focus', 'light gray', 'dark blue', 'standout'),
        ('foot', 'light gray', 'black'),
        ('head', 'yellow', 'black', 'standout'),
        ('key', 'light cyan', 'black','underline'),
        ('odd row', 'light gray', 'dark gray'),
        ('title', 'white', 'black', 'bold'),
        (None, 'dark red', 'light gray'),  # Make it visible
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
            return urwid.Padding(w, left=1, right=1)

        self.data = data
        self.topnode = ContainerNode(self.data)
        self.container_tree_list_box = ContainerTreeListBox(urwid.TreeWalker(self.topnode))
        self.container_detail_box = pad(self.topnode.get_container_info_widget())
        self.container_tree_list_box.on_listbox_node_change = self.on_listbox_node_change

        self.columns = urwid.Columns(
            [
                urwid.LineBox(self.container_tree_list_box),
                (80, urwid.LineBox(self.container_detail_box)),
             ])
        self.columns.set_focus_column(0)

        footer = urwid.AttrWrap(urwid.Text(self.footer_text), 'foot')

        rows = [
            [2, urwid.Text('l'), urwid.Text('c'), urwid.Text('r') ],
        ]
        header = urwid.BoxAdapter(make_grid(rows), height = 2)
        header = urwid.AttrWrap(header, 'head')

        self.topmost = urwid.Frame(urwid.AttrWrap(self.columns, 'body'), header=header, footer=footer)

    def set_container_tree_filter_regex(self, regex):
        if not isinstance(regex, basestring):
            regex = regex[0]
        reg = re.compile(regex)
        filt = lambda c: reg.search(c.metadata.name) is None
        Container.filters = [filt]  # FIXME
        self.topnode.forget_children()
        self.container_tree_list_box.focus_home((0,0))
        self.container_tree_list_box.collapse_focus_parent((0,0))

    def main(self):
        self.loop = urwid.MainLoop(self.topmost, self.palette, unhandled_input=self.unhandled_input, pop_ups=True)
        loop = self.loop
        self.loop.run()

    def unhandled_input(self, k):
        if k in ('q','Q'):
            raise urwid.ExitMainLoop()
        if k.lower() == 'f':
            if Container.filters:  # FIXME: no easy way to get current filter
                regex = Container.filters[0]
            else:
                regex = ''
            d = EditDialog(50, 10, initial_text='',
                           header_text='Filter Object Tree',
                           editor_label='python regex to apply to attribute name: ',
                           loop=self.loop)
            urwid.connect_signal(d, 'commit_text', self.set_container_tree_filter_regex)
            d.show()

    def on_listbox_node_change(self, *args, **kwargs):
        node = args[0]
        w = node.get_container_info_widget()
        self.container_detail_box.original_widget = w

def _main(*args, **kwargs):
    root = Container(urwid)
    PynautTreeBrowser(root).main()

def main():
    curses.wrapper(_main)

browse = main
main()
