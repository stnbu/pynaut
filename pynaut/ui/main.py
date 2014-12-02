# -*- coding: utf-8 -*-
import __builtin__
from pynaut import Container
import urwid
import os
import re
import logging
import curses
import types
from collections import OrderedDict

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
log_file_path = os.path.join('/tmp/.urwid_devel.log')
fh = logging.FileHandler(log_file_path)
file_formatter = logging.Formatter('%(asctime)s %(name)-12s(%(lineno)s): %(levelname)-8s %(message)s')
fh.setFormatter(file_formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

from urwid.wimp import SelectableIcon

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

class DialogBase(urwid.WidgetWrap):

    __metaclass__ = urwid.signals.MetaSignals
    signals = ['commit']

    parent = None
    def __init__(self, width, height, data, header_text=None, loop=None):
        if loop is None:
            raise ValueError('loop is a required argument.')

        width = int(width)
        if width <= 0:
            width = ('relative', 80)
        height = int(height)
        if height <= 0:
            height = ('relative', 80)

        self.body = self.make_body(data)

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

    def make_body(self, data):
        'please implement'

    def callback(self):
        'please implement'

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
        urwid.emit_signal(self, 'commit', self.callback())
        self._button(self, *args, **kwargs)

    def on_cancel(self, *args, **kwargs):
        self._button(self, *args, **kwargs)

    def show(self):
        self.loop.widget = self.view

class AttrTypeDialog(DialogBase):
    def make_body(self, data):
        self.checkboxes = []
        for label, values in data.iteritems():
            _unused, state = values
            self.checkboxes.append(urwid.CheckBox(label, state=state))
        return urwid.ListBox(urwid.SimpleListWalker(self.checkboxes))
    def callback(self):
        return self.checkboxes

class EditDialog(DialogBase):
    def make_body(self, data):
        edit_text, editor_label = data
        self.edit = urwid.Edit(edit_text=edit_text)
        body = urwid.ListBox(urwid.SimpleListWalker([
            urwid.AttrWrap(urwid.Text(editor_label), None, 'reveal focus'),
            urwid.AttrWrap(self.edit, None, 'reveal focus'),
        ]))
        return body
    def callback(self):
        return self.edit.get_edit_text()

class PynautTreeWidget(urwid.TreeWidget):
    leaf_container_icon = SelectableIcon(' ', 0)

    def __init__(self, node):
        self.__super.__init__(node)
        self._w = urwid.AttrWrap(self._w, None)
        self.flagged = False
        self.update_w()
        self.expanded = False
        self.flagged_nodes = set()
        self.update_expanded_icon()
        self.is_leaf = node.container_object.is_leaf

    def selectable(self):
        return True

    def keypress(self, size, key):
        self.update_expanded_icon()
        key = self.__super.keypress(size, key)
        if key in ('+', 'enter', '\\'):
            self.expanded = True
            self.update_expanded_icon()
        elif key in ('left', '-'):
            self.expanded = False
            self.update_expanded_icon()
        else:
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
        if self.flagged:
            self._w.attr = 'flagged'
            self._w.focus_attr = 'flagged focus'
        else:
            self._w.attr = 'body'
            self._w.focus_attr = 'focus'

    def load_inner_widget(self):
        return urwid.Text(self.get_node().get_value()['name'])

    def update_expanded_icon(self):
        container_object = self.get_node().get_value()
        if container_object.is_leaf:
            self._w.base_widget.widget_list[0] = self.leaf_container_icon
        else:
            self._w.base_widget.widget_list[0] = [
                self.unexpanded_icon, self.expanded_icon][self.expanded]





class ContainerNode(urwid.ParentNode):

    def __init__(self, *args, **kwargs):
        self.container_object = args[0]
        urwid.ParentNode.__init__(self, *args, **kwargs)
        self.my_widget = None

    def forget_children(self):
        self._child_keys = None
        self._children = {}

    def load_widget(self):
        self.my_widget = PynautTreeWidget(self)
        return self.my_widget

    def load_child_keys(self):
        return range(len(self.container_object.children))

    def load_child_node(self, key):
        childdata = self.container_object.children[key]
        childclass = ContainerNode
        return childclass(childdata,
                          parent=self,
                          key=key,
                          depth=self.get_depth()+1)

    def get_container_info_widget(self):
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

        rows = []
        c = 0
        for height, name, value in metadata:
            if c % 2:
                color = 'odd row'
            else:
                color = 'even row'
            c += 1
            name = urwid.AttrMap(urwid.Text(unicode(name)), color)
            value = urwid.AttrMap(urwid.Text(unicode(value)), color)
            rows.append([height, name, value])
        body = make_grid(rows)
        return body


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

        self.original_filters = []
        self.original_filters[:] = Container.filters
        self.grep_filter = None
        self.type_filter = None

        self.type_filter_states = OrderedDict()
        ## format:
        #self.type_filter_states = {
        #    'Friendly Name': (SomeType, True),
        #    # also...
        #    'Friendly Name Two': ((SomeType1, SomeType2), True),
        builtin_types = set([t for t in vars(types).values() if t.__class__ is types.TypeType])  # FIXME
        builtin_types = OrderedDict(sorted([(x.__name__, (x, True)) for x in builtin_types]))
        self.type_filter_states.update(builtin_types)
        self.attr_filter_reg = None
        self.data = data
        self.topnode = ContainerNode(self.data)
        self.container_tree_list_box = ContainerTreeListBox(urwid.TreeWalker(self.topnode))
        self.container_detail_box = urwid.WidgetPlaceholder(self.topnode.get_container_info_widget())
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

    def on_filter_change(self):
        Container.filters[:] = self.original_filters
        for filter in  self.type_filter, self.grep_filter:
            if filter is not None:
                Container.filters.append(filter)
        self.topnode.forget_children()
        self.container_tree_list_box.focus_home((0,0))
        self.container_tree_list_box.collapse_focus_parent((0,0))
        omnilog.error('1  '+str(Container.filters))

    def set_attr_type_filters(self, *args, **kwargs):
        checkboxes, = args
        for checkbox in checkboxes:
            types = self.type_filter_states[checkbox.label][0]
            self.type_filter_states[checkbox.label] = (types, checkbox.state)
        enabled_types = []
        for label, values in self.type_filter_states.iteritems():
            types, enabled = values
            if not enabled:
                continue
            if not isinstance(types, tuple):
                types = (types,)
            enabled_types.extend(types)
        enabled_types = tuple(enabled_types)
        omnilog.error(str(enabled_types))
        self.type_filter = lambda c: isinstance(c.obj, enabled_types)
        self.on_filter_change()

    def set_container_tree_filter_regex(self, regex):
        if not isinstance(regex, basestring):
            regex = regex[0]
        self.attr_filter_reg = re.compile(regex)
        self.grep_filter = lambda c: self.attr_filter_reg.search(c.metadata.name) is None
        self.on_filter_change()

    def main(self):
        self.loop = urwid.MainLoop(self.topmost, self.palette, unhandled_input=self.unhandled_input, pop_ups=True)
        loop = self.loop
        self.loop.run()

    def unhandled_input(self, k):
        if k in ('q','Q'):
            raise urwid.ExitMainLoop()
        if k.lower() == 'f':
            if self.attr_filter_reg is None:
                edit_text = ''
            else:
                edit_text = self.attr_filter_reg.pattern
            d = EditDialog(50, 10, data=(edit_text, 'python regex to apply to attribute name: '),
                           header_text='Filter Object Tree',
                           loop=self.loop)
            urwid.connect_signal(d, 'commit', self.set_container_tree_filter_regex)
            d.show()
        if k.lower() == 't':
            d = AttrTypeDialog(50, 30, data=self.type_filter_states, header_text='Choose Attribute Types to Include', loop=self.loop)
            urwid.connect_signal(d, 'commit', self.set_attr_type_filters)
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
