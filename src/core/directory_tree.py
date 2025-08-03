from gi.repository import Gio, Gtk, GLib, GObject

class FileListItem(GObject.Object):
    def __init__(self, file: Gio.File, **kwargs):
        super().__init__(**kwargs)
        self.file = file
        self.is_dir = file.query_file_type(Gio.FileQueryInfoFlags.NONE, None) == Gio.FileType.DIRECTORY
        file_info = file.query_info("standard::display-name", Gio.FileQueryInfoFlags.NONE, None)
        self.display_name = file_info.get_display_name() if file_info else ""

def create_child_model_func(item):
    parent_item = item
    if not parent_item or not parent_item.is_dir:
        return None

    child_list_store = Gio.ListStore.new(FileListItem)
    try:
        enumerator = parent_item.file.enumerate_children(
            "standard::name,standard::type",
            Gio.FileQueryInfoFlags.NONE,
            None
        )
        while True:
            file_info = enumerator.next_file(None)
            if not file_info:
                break
            child_file = parent_item.file.get_child(file_info.get_name())
            child_list_store.append(FileListItem(file=child_file))
    except GLib.Error as e:
        print(f"Error reading directory: {e.message}")
        pass
    return child_list_store
