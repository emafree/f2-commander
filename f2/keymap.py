from textual.binding import Binding

BINDINGS_VI = [
    Binding("?", "help", "Help"),
    Binding("b", "go_to_bookmark", "Bookmarks"),
    Binding("v", "view", "View"),
    Binding("e", "edit", "Edit"),
    Binding("c", "copy", "Copy"),
    Binding("m", "move", "Move"),
    Binding("ctrl+n", "mkdir", "MkDir"),
    Binding("D", "delete", "Delete"),
    Binding("x", "shell", "Shell"),
    Binding("q", "quit", "Quit"),
]

BINDINGS_FN = [
    Binding("f1", "help", "Help"),
    Binding("f2", "go_to_bookmark", "Bookmarks"),
    Binding("f3", "view", "View"),
    Binding("f4", "edit", "Edit"),
    Binding("f5", "copy", "Copy"),
    Binding("f6", "move", "Move"),
    Binding("f7", "mkdir", "MkDir"),
    Binding("f8", "delete", "Delete"),
    Binding("f9", "shell", "Shell"),
    Binding("f10", "quit", "Quit"),
]
