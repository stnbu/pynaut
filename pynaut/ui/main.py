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
from IPython import embed
import pty
from random import choice
import atexit

logger = logging.getLogger(__name__)

from urwid.vterm import KEY_TRANSLATIONS  # FIXME: monkeypatch badness
KEY_TRANSLATIONS['enter'] = chr(10)
KEY_TRANSLATIONS['home'] = chr(27) + '[H'
KEY_TRANSLATIONS['end'] = chr(27) + '[F'

from urwid.wimp import SelectableIcon

palette_dict = {
    'body': ('black', 'light gray'),
    'dirmark': ('black', 'dark cyan', 'bold'),
    'error': ('dark red', 'light gray'),
    'even row': ('dark gray', 'light gray'),
    'flag': ('dark gray', 'light gray'),
    'flagged focus': ('yellow', 'dark cyan', ('bold','standout','underline')),
    'flagged': ('black', 'dark green', ('bold','underline')),
    'focus': ('light gray', 'dark blue', 'standout'),
    'foot': ('light gray', 'black'),
    'head': ('yellow', 'black', 'standout'),
    'key': ('light cyan', 'black','underline'),
    'odd row': ('light gray', 'dark gray'),
    'title': ('white', 'black', 'bold'),
}

config = {
    'prompt_on_quit': False,
}


def get_palette():

    from pudb.theme import get_palette, THEMES
    p = get_palette(False, choice(THEMES))
    for l in p:
        palette_dict[l[0]] = l[1:]

    palette = []
    for name, value in palette_dict.iteritems():
        palette.append((name,) + value)

    return palette


    #colors = ['light red', 'light magenta', 'dark magenta', 'brown', 'dark red', 'light magenta', 'yellow',
    #        'dark gray', 'dark blue', 'light cyan', 'black', 'dark cyan', 'white', 'light gray', 'dark green']
    #names = ['focused return label', 'doublestring', 'focus', 'var label', 'focused current frame name', 'current breakpoint focused source', 'title', 'focused frame location', 'source', 'focused current frame location', 'string', 'command line prompt', 'background', 'foot', 'search not found', 'fixed value', 'focused sidebar', 'breakpoint focused source', 'classname', 'name', 'frame class', 'button', 'focused current breakpoint', 'return value', 'flagged', 'current frame name', 'focused command line output', 'command line error', 'focused highlighted var label', 'label', 'highlighted var label', 'body', 'current highlighted source', 'focused current frame class', 'key', 'hotkey', 'command line input', 'selectable', 'command line focused button', 'focused highlighted var value', 'highlighted source', 'focused source', 'focused selectable', 'comment', 'search box', 'variables', 'odd row', 'header', 'line number', 'focused var value', 'command line clear button', 'frame name', 'flagged focus', 'frame location', 'literal', 'even row', 'focused command line error', 'head', 'focused frame class', 'focused return value', 'dirmark', 'flag', 'singlestring', 'current frame class', 'keyword', 'command line output', 'focused var label', 'breakpoint marker', 'value', 'focused frame name', 'error', 'dialog title', 'kw_namespace', 'warning', 'breakpoint source', 'variable separator', 'current focused source', 'punctuation', 'group head', 'var value', 'current breakpoint source', 'current frame location', 'current source', 'focused breakpoint', 'command line edit', 'docstring', 'current breakpoint', 'focused button', 'focused command line input', 'breakpoint', 'stack', 'highlighted var value', 'return label']
    #def get_pair():
    #    dark = choice([c for c in colors if 'dark' in c])
    #    light = choice([c for c in colors if 'dark' not in c])
    #    return dark, light
    #palette = []
    #for name in names:
    #    palette.append((name,)+get_pair())
    #return palette



def next_in_pile(pile, size, key, loop):

    item_rows = None
    i = pile.focus_position
    if pile._command_map[key] == 'j':
        candidates = range(i-1, -1, -1)
    else:
        candidates = range(i+1, len(pile.contents))
    if not item_rows:
        item_rows = pile.get_item_rows(size, focus=True)
    for j in candidates:
        if not pile.contents[j][0].selectable():
            continue
        pile._update_pref_col_from_focus(size)   # ??
        pile.focus_position = j
        if not hasattr(pile.focus, 'move_cursor_to_coords'):
            return
        rows = item_rows[j]
        if pile._command_map[key] == 'j':
            rowlist = range(rows-1, -1, -1)
        else:
            rowlist = range(rows)
        for row in rowlist:
            tsize = pile.get_item_size(size, j, True, item_rows)
            if pile.focus_item.move_cursor_to_coords(
                    tsize, pile.pref_col, row):
                break
        return
    return key


class IPyTerminal(urwid.Terminal):

    #def __init__(self, *args, **kwargs):
    #    urwid.Terminal.__init__(self, *args, **kwargs)

    def spawn(self):
        self.master, slave_fd = pty.openpty()
        self.pid = os.fork()
        if self.pid == pty.CHILD:
            os.setsid()
            os.close(self.master)
            os.dup2(slave_fd, pty.STDIN_FILENO)
            os.dup2(slave_fd, pty.STDOUT_FILENO)
            os.dup2(slave_fd, pty.STDERR_FILENO)
            if (slave_fd > pty.STDERR_FILENO):
                os.close (slave_fd)
            tmp_fd = os.open(os.ttyname(pty.STDOUT_FILENO), os.O_RDWR)
            os.close(tmp_fd)
        else:
            os.close(slave_fd)
        if self.pid == 0:
            try:
                self.command()
            except:
                sys.stderr.write(traceback.format_exc())
                sys.stderr.flush()
        if self.main_loop is None:
            fcntl.fcntl(self.master, fcntl.F_SETFL, os.O_NONBLOCK)
        atexit.register(self.terminate)

    #def keypress(self, size, key):
    #    if key == 'ctrl b':
    #        self.term.scroll_buffer(up=True, lines=self.height-1)
    #    elif key == 'ctrl f':
    #        self.term.scroll_buffer(up=False, lines=self.height-1)
    #    return urwid.Terminal.keypress(self, size, key)

    #def set_termsize(self, width, height):
    #    return  # broken for me!

    #def touch_term(self, width, height):
    #    if not self.term:
    #        self.term = urwid.TermCanvas(width, height, self)
    #        no_resize = True
    #    if self.pid is None:
    #        self.spawn()
    #        process_opened = True
    #    no_resize = False
    #    process_opened = False
    #    if self.width == width and self.height == height:
    #        return
    #    self.set_termsize(width, height)
    #    if no_resize:
    #        self.term.resize(width, height)
    #    self.width = width
    #    self.height = height
    #    if process_opened:
    #        self.add_watch()

    def touch_term(self, width, height):
        if not self.term:
            self.term = urwid.TermCanvas(width, height, self)
        process_opened = False
        if self.pid is None:
            self.spawn()
            process_opened = True
        self.set_termsize(width, height)
        if self.width == width and self.height == height:
            return
        else:
            self.term.resize(width, height)
        self.width = width
        self.height = height
        if process_opened:
            self.add_watch()

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

        self.frame = DialogFrame(self.body, focus_part = 'body', escape=self.on_negatory)
        if header_text is not None:
            self.frame.header = urwid.Pile( [urwid.Text(header_text),
                urwid.Divider(u'\u2550')] )
        w = self.frame

        # pad area around listbox
        w = urwid.Padding(w, ('fixed left',2), ('fixed right',2))
        w = urwid.Filler(w, ('fixed top',1), ('fixed bottom',1))
        w = urwid.AttrMap(w, 'body')
        w = urwid.LineBox(w)
        # "shadow" effect
        w = urwid.Columns( [w,('fixed', 1, urwid.AttrMap(
            urwid.Filler(urwid.Text(('border',' ')), "top")
            ,'shadow'))])
        w = urwid.Frame( w, footer = urwid.AttrMap(urwid.Text(('border',' ')),'shadow'))
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
            b = urwid.AttrMap( b, 'button normal','button select' )
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
        return urwid.Filler(urwid.Text(data))

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
            urwid.AttrMap(urwid.Text(editor_label), 'reveal focus'),
            urwid.AttrMap(self.edit, 'reveal focus'),
        ]))
        return body
    def callback(self):
        return self.edit.get_edit_text()

class PynautTreeWidget(urwid.TreeWidget):
    leaf_container_icon = SelectableIcon(' ', 0)

    def __init__(self, node):
        self.__super.__init__(node)
        self._w = urwid.AttrMap(self._w, None)
        self.flagged = False
        self.update_w()
        self.expanded = False
        self.flagged_nodes = set()
        self.update_expanded_icon()
        self.is_leaf = node.container_object.is_leaf

    def selectable(self):
        return True

    def toggle(self):
        self.expanded = not self.expanded
        self.update_expanded_icon()

    def keypress(self, size, key):
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
    #palette = [
    #    ('body', 'black', 'light gray'),
    #    ('dirmark', 'black', 'dark cyan', 'bold'),
    #    ('error', 'dark red', 'light gray'),
    #    ('even row', 'dark gray', 'light gray'),
    #    ('flag', 'dark gray', 'light gray'),
    #    ('flagged focus', 'yellow', 'dark cyan', ('bold','standout','underline')),
    #    ('flagged', 'black', 'dark green', ('bold','underline')),
    #    ('focus', 'light gray', 'dark blue', 'standout'),
    #    ('foot', 'light gray', 'black'),
    #    ('head', 'yellow', 'black', 'standout'),
    #    ('key', 'light cyan', 'black','underline'),
    #    ('odd row', 'light gray', 'dark gray'),
    #    ('title', 'white', 'black', 'bold'),
    #    ]


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

        self.footer = urwid.AttrMap(urwid.Text(self.footer_text), 'foot')

        rows = [
            [2, urwid.Text('l'), urwid.Text('c'), urwid.Text('r') ],
        ]
        header = urwid.BoxAdapter(make_grid(rows), height = 2)
        self.header = urwid.AttrMap(header, 'head')

        self.main_ = urwid.Frame(urwid.AttrMap(self.columns, 'body'), header=self.header, footer=self.footer)

        self.term = urwid.WidgetPlaceholder(urwid.Filler(urwid.Text('')))
        self.term = urwid.AttrMap(self.term, 'terminal')
        self.topmost = urwid.LineBox(
            urwid.Pile([
                ('weight', 1, self.main_),
                (15, self.term),
            ], focus_item=1),
        )

    def embed(self):
        pass
        #embed(header='', banner1='', banner2='')

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
        self.grep_filter = lambda c: self.attr_filter_reg.search(c.metadata.name) is None
        self.on_filter_change()

    def main(self):
        from urwid.curses_display import Screen as CursesScreen
        self.loop = urwid.MainLoop(self.topmost, get_palette(), unhandled_input=self.unhandled_input, pop_ups=True, handle_mouse=False, screen=CursesScreen())
        self.term.original_widget = IPyTerminal(self.embed, main_loop=self.loop)
        self.loop.run()

    def quit(self):
        raise urwid.ExitMainLoop()

    def user_quit(self, response):
        if response is True:
            self.quit()

    def unhandled_input(self, k):
        if not isinstance(k, basestring):
            return k
        if k.lower() == 'q':
            if not config['prompt_on_quit']:
                self.quit()
            dialog = YesNoDialog(30, 10, data='Are you sure you want to quit?',
                            header_text='Quitting Application', loop=self.loop)
            urwid.connect_signal(dialog, 'commit', self.user_quit)
            dialog.show()
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
        if k.lower() == 'j':
            size = self.loop.screen.get_cols_rows()
            pile = self.topmost.original_widget
            next_in_pile(pile, size, key=k, loop=self.loop)
        if k.lower() == 'k':
            size = self.loop.screen.get_cols_rows()
            pile = self.topmost.original_widget
            next_in_pile(pile, size, key=k, loop=self.loop)

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

if __name__ == '__main__':
    main()
