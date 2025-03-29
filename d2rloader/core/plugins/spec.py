from pluggy import HookspecMarker

spec = HookspecMarker("d2rloader")

# types are removed here to prevent those nasty cyclic import errors
# 'state' always implies the D2RLoaderState


@spec
def d2rloader_register_plugin():
    """Hook for adding a new entry to the QMenu item.

    A new Section 'Plugins' will be created if it doesn't exist and you plugin will be
    placed in it
    """
    pass


@spec
def d2rloader_mainwindow_plugin_menu(state, parent, menu):
    """Hook for adding a new entry to the QMenu item.

    A new Section 'Plugins' will be created if it doesn't exist and you plugin will be
    placed in it
    """
    pass


@spec
def d2rloader_table_context_menu(widget, item, state):
    """Hook for extending the right click menu in the accounts table"""
    pass


@spec
def d2rloader_table_right_button_menu(widget, state):
    """Hook for extending the right aligned button menu"""
    pass


@spec
def d2rloader_table_left_button_menu(widget, state):
    """Hook for extending the left aligned button menu"""
    pass


@spec
def d2rloader_info_tabbar(state, tabbar):
    """Hook for extending the info tabbar"""
    pass


@spec
def d2rloader_example_hook(state):
    """An example hook used in the examples"""
    pass
