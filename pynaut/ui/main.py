# -*- coding: utf-8 -*-

try:
    import __builtin__
    builtins = __builtin__
except ImportError:
    import builtins
from pynaut import Container
import urwid
import os
import re
import logging
import curses
import types
from collections import OrderedDict
from IPython import embed
import pty
from random import choice
import atexit
from urwid.vterm import KEY_TRANSLATIONS
from urwid.wimp import SelectableIcon

# FIXME: monkeypatch badness
KEY_TRANSLATIONS['enter'] = chr(10)
KEY_TRANSLATIONS['home'] = chr(27) + '[H'
KEY_TRANSLATIONS['end'] = chr(27) + '[F'

LOOP = None

logger = logging.getLogger(__name__)

config = {
    'prompt_on_quit': False,
}

palette = [

    # palette stolen from pudb project:
    # https://pypi.python.org/pypi/pudb

    ('comment', 'light gray', 'dark blue'),
    ('punctuation', 'light gray', 'dark blue'),
    ('search box', 'black', 'dark cyan'),
    ('variables', 'black', 'dark cyan'),
    ('focused var label', 'dark blue', 'dark green'),
    ('doublestring', 'light magenta,bold', 'dark blue'),
    ('focused command line output', 'black', 'dark green'),
    ('var label', 'dark blue', 'dark cyan'),
    ('header', 'black', 'light gray', 'standout'),
    ('line number', 'light gray', 'dark blue'),
    ('warning', 'white,bold', 'dark red', 'standout'),
    ('focused current frame class', 'dark blue', 'dark green'),
    ('command line clear button', 'white,bold', 'dark blue'),
    ('breakpoint source', 'yellow,bold', 'dark red'),
    ('stack', 'black', 'dark cyan'),
    ('focused current frame name', 'white,bold', 'dark green', 'bold'),
    ('current breakpoint focused source', 'white', 'dark red'),
    ('focused current frame location', 'light cyan', 'dark green'),
    ('command line focused button', 'light cyan', 'black'),
    ('frame name', 'black', 'dark cyan'),
    ('current focused source', 'white,bold', 'dark cyan'),
    ('current frame location', 'light cyan', 'dark cyan'),
    ('command line error', 'light red,bold', 'dark blue'),
    ('focused highlighted var label', 'white', 'dark green'),
    ('frame location', 'light cyan', 'dark cyan'),
    ('label', 'black', 'light gray'),
    ('source', 'yellow,bold', 'dark blue'),
    ('literal', 'light magenta, bold', 'dark blue'),
    ('highlighted var value', 'black', 'dark cyan'),
    ('group head', 'dark blue,bold', 'light gray'),
    ('focused sidebar', 'yellow,bold', 'light gray', 'standout'),
    ('var value', 'black', 'dark cyan'),
    ('focused command line error', 'black', 'dark green'),
    ('variable separator', 'dark cyan', 'light gray'),
    ('focused return value', 'black', 'dark green'),
    ('current source', 'black', 'dark cyan'),
    ('focused breakpoint', 'black', 'dark green'),
    ('focused frame class', 'dark blue', 'dark green'),
    ('command line edit', 'yellow,bold', 'dark blue'),
    ('string', 'light magenta,bold', 'dark blue'),
    ('focused return label', 'light gray', 'dark blue'),
    ('command line prompt', 'white,bold', 'dark blue'),
    ('current highlighted source', 'white', 'dark cyan'),
    ('highlighted var label', 'white', 'dark cyan'),
    ('docstring', 'light magenta,bold', 'dark blue'),
    ('current breakpoint', 'white,bold', 'dark cyan'),
    ('focused button', 'light cyan', 'black'),
    ('focused frame location', 'light cyan', 'dark green'),
    ('singlestring', 'light magenta,bold', 'dark blue'),
    ('focused command line input', 'light cyan,bold', 'dark green'),
    ('background', 'black', 'light gray'),
    ('breakpoint', 'black', 'dark cyan'),
    ('hotkey', 'black,underline', 'light gray', 'underline'),
    ('command line input', 'light cyan,bold', 'dark blue'),
    ('selectable', 'black', 'dark cyan'),
    ('search not found', 'white', 'dark red'),
    ('current breakpoint source', 'black', 'dark red'),
    ('fixed value', 'light gray', 'dark blue'),
    ('focused highlighted var value', 'black', 'dark green'),
    ('breakpoint focused source', 'black', 'dark red'),
    ('name', 'light cyan', 'dark blue'),
    ('keyword', 'white,bold', 'dark blue'),
    ('frame class', 'dark blue', 'dark cyan'),
    ('command line output', 'light cyan', 'dark blue'),
    ('button', 'white,bold', 'dark blue'),
    ('focused current breakpoint', 'white,bold', 'dark green', 'bold'),
    ('breakpoint marker', 'dark red', 'dark blue'),
    ('value', 'yellow,bold', 'dark blue'),
    ('highlighted source', 'black', 'dark magenta'),
    ('current frame class', 'dark blue', 'dark cyan'),
    ('focused frame name', 'black', 'dark green'),
    ('return label', 'white', 'dark blue'),
    ('return value', 'black', 'dark cyan'),
    ('focused source', 'black', 'dark green'),
    ('current frame name', 'white,bold', 'dark cyan'),
    ('focused var value', 'black', 'dark green'),
    ('dialog title', 'white,bold', 'dark cyan'),
    ('focused selectable', 'black', 'dark green'),
    ####
    ('object descr box', 'white', 'dark cyan'),
    ('activity area', 'black', 'dark cyan'),
    ('border', 'dark cyan', 'dark blue'),
    ('tree row', 'dark blue', 'dark cyan'),
    ('flagged', 'dark blue', 'dark green'),
    ('flagged focus', 'black', 'dark green'),
    ('focus', 'black', 'dark blue'),
    ('title', 'black,bold', 'light gray'),
    ('key', 'light cyan', 'light gray'),
]


class BorderedLineBox(urwid.LineBox):

    def __init__(self, original_widget, title="",
                 tlcorner=u'┌', tline=u'─', lline=u'│',
                 trcorner=u'┐', blcorner=u'└', rline=u'│',
                 bline=u'─', brcorner=u'┘', border_color=None):
        tline, bline = urwid.AttrMap(urwid.Divider(tline), border_color), urwid.AttrMap(urwid.Divider(bline), border_color)
        lline, rline = urwid.AttrMap(urwid.SolidFill(lline), border_color), urwid.AttrMap(urwid.SolidFill(rline), border_color)
        tlcorner, trcorner = urwid.AttrMap(urwid.Text(tlcorner), border_color), urwid.AttrMap(urwid.Text(trcorner), border_color)
        blcorner, brcorner = urwid.AttrMap(urwid.Text(blcorner), border_color), urwid.AttrMap(urwid.Text(brcorner), border_color)
        self.title_widget = urwid.AttrMap(urwid.Text(self.format_title(title)), border_color)
        self.tline_widget = urwid.Columns([
            tline,
            ('flow', self.title_widget),
            tline,
        ])
        top = urwid.Columns([
            ('fixed', 1, tlcorner),
            self.tline_widget,
            ('fixed', 1, trcorner)
        ])
        middle = urwid.Columns([
            ('fixed', 1, lline),
            original_widget,
            ('fixed', 1, rline),
        ], box_columns=[0, 2], focus_column=1)
        bottom = urwid.Columns([
            ('fixed', 1, blcorner), bline, ('fixed', 1, brcorner)
        ])
        pile = urwid.Pile([('flow', top), middle, ('flow', bottom)], focus_item=1)
        urwid.WidgetDecoration.__init__(self, original_widget)
        urwid.WidgetWrap.__init__(self, pile)


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
        if key in ('tab', 'up', 'down'):
            if self.focus_part == 'body':
                if key in ('tab', 'down'):
                    self.set_focus('footer')
            elif self.focus_part == 'footer':
                if key in ('tab', 'up'):
                    self.set_focus('body')
        elif key in ['esc',]:
            self.escape()
        return self.__super.keypress(size, key)

class DialogBase(urwid.WidgetWrap):

    __metaclass__ = urwid.signals.MetaSignals
    signals = ['commit']

    parent = None
    def __init__(self, width, height, data, header_text=None, loop=None, buttons=None):
        if loop is None:
            raise ValueError('loop is a required argument.')

        width = int(width)
        if width <= 0:
            width = ('relative', 80)
        height = int(height)
        if height <= 0:
            height = ('relative', 80)

        self.body = self.make_body(data)

        self.frame = DialogFrame(self.body, focus_part='body', escape=self.on_negatory)
        if header_text is not None:
            self.frame.header = urwid.Pile( [urwid.AttrMap(urwid.Text(header_text), 'background'),
                urwid.Divider(u'\u2550')] )
        w = self.frame

        # pad area around listbox
        w = urwid.Padding(w, ('fixed left',2), ('fixed right',2))
        w = urwid.Filler(w, ('fixed top',1), ('fixed bottom',1))
        w = urwid.AttrMap(w, 'background')  # ?????
        w = BorderedLineBox(w, border_color='border')
        self.loop = loop
        self.parent = self.loop.widget
        w = urwid.Overlay(w, self.parent, 'center', width+2, 'middle', height+2)
        self.view = w
        self.buttons = buttons
        if self.buttons is None:
            self.buttons = [("OK", True, self.on_affirmative), ("Cancel", False, self.on_negatory)]
        elif isinstance(self.buttons, basestring):
            if self.buttons.lower() in ('yesno', 'yes/no', 'yes-no'):
                self.buttons = [("Yes", True, self.on_affirmative), ("No", False, self.on_negatory)]
            elif self.buttons.lower() in ('okcancel', 'ok/cancel', 'ok-cancel'):
                self.buttons = [("OK", True, self.on_affirmative), ("Cancel", False, self.on_negatory)]
        self.add_buttons(self.buttons)

        self.exitcode = None

        urwid.WidgetWrap.__init__(self, self.view)

    def make_body(self, data):
        'please implement'

    def callback(self):
        'please implement'

    def add_buttons(self, buttons):
        l = []
        for name, exitcode, callback in buttons:
            b = urwid.Button(name, callback, user_data=exitcode)
            b.exitcode = exitcode
            b = urwid.AttrMap( b, 'button', 'focusted button' )
            l.append( b )
        self.buttons = urwid.GridFlow(l, 10, 3, 1, 'center')
        self.frame.footer = urwid.Pile( [ urwid.Divider(u'\u2500'),
            self.buttons ], focus_item = 1)

    def _button(self, *args, **kwargs):
        if len(args) == 3:
            _class, button, _status = args
            self.exitcode = button.exitcode
        self.loop.widget = self.parent

    def on_affirmative(self, *args, **kwargs):
        self._button(self, *args, **kwargs)
        urwid.emit_signal(self, 'commit', self.callback())

    def on_negatory(self, *args, **kwargs):
        self._button(self, *args, **kwargs)

    def show(self):
        self.loop.widget = self.view

class YesNoDialog(DialogBase):

    def __init__(self, *args, **kwargs):
        kwargs['buttons'] = 'yes/no'
        DialogBase.__init__(self, *args, **kwargs)

    def make_body(self, data):
        return urwid.AttrMap(urwid.Filler(urwid.Text(data)), 'background')

    def callback(self, *args, **kwargs):
        return self.exitcode

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
            urwid.AttrMap(urwid.Text(editor_label), 'dialog title'),
            urwid.AttrMap(self.edit, 'command line input'),
        ]))
        return body
    def callback(self):
        return self.edit.get_edit_text()

class PynautTreeWidget(urwid.TreeWidget):
    unexpanded_icon = urwid.AttrMap(urwid.TreeWidget.unexpanded_icon,
        'tree row')
    expanded_icon = urwid.AttrMap(urwid.TreeWidget.expanded_icon,
        'tree row')
    leaf_container_icon = SelectableIcon(' ', 0)

    def __init__(self, node):
        self.__super.__init__(node)
        self._w = urwid.AttrMap(self._w, None)
        self.flagged = False
        self.expanded = False
        self.flagged_nodes = set()
        self.update_expanded_icon()
        self.is_leaf = node.container_object.is_leaf
        self.update_w()

    def selectable(self):
        return True

    def toggle(self):
        self.expanded = not self.expanded
        self.update_expanded_icon()

    def keypress(self, size, key):
        self.update_w()
        self.update_expanded_icon()
        key = self.__super.keypress(size, key)
        if key in ('+', 'enter',):
            self.expanded = True
            self.update_expanded_icon()
        elif key in ('left', '-'):
            self.expanded = False
            self.update_expanded_icon()
        elif key in ('\\',):
            self.toggle()
        elif key == " ":
            self.flagged = not self.flagged
            container_object = self.get_node().get_value()
            if self.flagged:
                self.flagged_nodes.add(container_object)
            else:
                if container_object in self.flagged_nodes:
                    self.flagged_nodes.remove(container_object)
        else:
            return key

    def update_w(self):
        if self.flagged:
            self._w.attr = 'flagged'
            self._w.focus_attr = 'flagged focus'
        else:
            self._w.attr = 'tree row'
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
        self.children = list(self.container_object.children)
        urwid.ParentNode.__init__(self, *args, **kwargs)
        self.my_widget = None

    def forget_children(self):
        self._child_keys = None
        self._children = {}

    def load_widget(self):
        self.my_widget = PynautTreeWidget(self)
        return self.my_widget

    def load_child_keys(self):
        return range(len(list(self.container_object.children)))

    def load_child_node(self, key):
        childdata = self.children[key]
        childclass = ContainerNode
        return childclass(childdata,
                          parent=self,
                          key=key,
                          depth=self.get_depth()+1)

    def get_container_info_widget(self):
        metadata = [
            # (height, label, value)
            (1, 'id()', self.container_object.id),
            (1, 'type', self.container_object.type),
            (1, 'file', self.container_object.file),
            (1, 'is module', self.container_object.ismodule),
            (1, 'parent module', self.container_object.parent_module),
            (3, 'names in sys.modules', self.container_object.imported_names),
            (3, 'known aliases', self.container_object.known_aliases),
            (20, 'doc', self.container_object.doc),
        ]

        rows = []
        c = 0
        for height, name, value in metadata:
            if c % 2:
                color = 'odd row'
            else:
                color = 'even row'
            c += 1

            name = urwid.AttrMap(urwid.Text(unicode(name)), 'var label')
            value = urwid.AttrMap(urwid.Text(unicode(value)), 'var value')
            rows.append([height, name, value])
        body = make_grid(rows)
        body = urwid.AttrMap(body, 'object descr box')
        return body


class ContainerTreeListBox(urwid.TreeListBox):

    on_listbox_node_change = None

    def change_focus(self, *args, **kwargs):
        node = args[1]
        if self.on_listbox_node_change is not None:
            self.on_listbox_node_change(node)
        return urwid.TreeListBox.change_focus(self, *args, **kwargs)

class PynautTreeBrowser:
    palette = palette
    terminal_header = [
        ('title', 'Pynaut Data Browser'), '    ',
        ]

    def __init__(self, data=None):
        self.original_filters = []
        self.original_filters[:] = Container.filters
        self.grep_filter = None
        self.type_filter = None
        self.type_filter_states = OrderedDict()
        builtin_types = set([t for t in vars(types).values() if t.__class__ is type])  # FIXME
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
                BorderedLineBox(self.container_tree_list_box, border_color='border'),
                (80, BorderedLineBox(self.container_detail_box, border_color='border')),
             ])
        self.columns.set_focus_column(0)
        self.footer = urwid.AttrMap(urwid.Text(self.terminal_header), 'header')
        rows = [
            [2, urwid.Text('l'), urwid.Text('c'), urwid.Text('r') ],
        ]
        header = urwid.BoxAdapter(make_grid(rows), height = 2)
        self.header = urwid.AttrMap(header, 'header')
        self.main_ = urwid.Frame(urwid.AttrMap(self.columns, 'activity area'), header=self.header, footer=self.footer)
        self.term = urwid.Terminal(command=self.embed, main_loop=LOOP)
        self.topmost = BorderedLineBox(
            urwid.Pile([
                ('weight', 1, self.main_),
                (10, self.term),
            ], focus_item=1),
            border_color='border',
        )
        self.topmost = urwid.AttrMap(self.topmost, 'background')

    def embed(self, *args, **kwargs):
        embed()

    def on_filter_change(self):
        Container.filters[:] = self.original_filters
        for filter in  self.type_filter, self.grep_filter:
            if filter is not None:
                Container.filters.append(filter)
        self.topnode.forget_children()
        self.container_tree_list_box.focus_home((0,0))
        self.container_tree_list_box.collapse_focus_parent((0,0))

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
        self.type_filter = lambda c: isinstance(c.obj, enabled_types)
        self.on_filter_change()

    def set_container_tree_filter_regex(self, regex):
        if not isinstance(regex, basestring):
            regex = regex[0]
        self.attr_filter_reg = re.compile(regex)
        self.grep_filter = lambda c: self.attr_filter_reg.search(c.name) is None
        self.on_filter_change()

    def main(self):
        global LOOP
        from urwid.curses_display import Screen as CursesScreen
        self.loop = urwid.MainLoop(widget=self.topmost,
                                   palette=self.palette,
                                   screen=CursesScreen(),
                                   handle_mouse=False,
                                   input_filter=None,
                                   unhandled_input=self.unhandled_input,
                                   pop_ups=True,)
        LOOP = self.loop
        self.loop.run()

    def quit(self):
        raise urwid.ExitMainLoop()

    def user_quit(self, response):
        if response is True:
            self.quit()

    def unhandled_input(self, k):
        if not isinstance(k, basestring):
            return k
        if k == 'q':
            if not config['prompt_on_quit']:
                self.quit()
            dialog = YesNoDialog(30, 10, data='Are you sure you want to quit?',
                            header_text='Quitting Application', loop=self.loop)
            urwid.connect_signal(dialog, 'commit', self.user_quit)
            dialog.show()
        elif k == 'f':
            if self.attr_filter_reg is None:
                edit_text = ''
            else:
                edit_text = self.attr_filter_reg.pattern
            d = EditDialog(50, 10, data=(edit_text, 'python regex to apply to attribute name: '),
                           header_text='Filter Object Tree',
                           loop=self.loop)
            urwid.connect_signal(d, 'commit', self.set_container_tree_filter_regex)
            d.show()
        elif k == 't':
            d = AttrTypeDialog(50, 30, data=self.type_filter_states, header_text='Choose Attribute Types to Include', loop=self.loop)
            urwid.connect_signal(d, 'commit', self.set_attr_type_filters)
            d.show()
        else:
            pass

    def on_listbox_node_change(self, *args, **kwargs):
        node = args[0]
        w = node.get_container_info_widget()
        self.container_detail_box.original_widget = w

def _main(*args, **kwargs):
    root = Container(urwid)
    PynautTreeBrowser(root).main()

def main():
    curses.wrapper(_main)
