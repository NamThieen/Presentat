# src/core/file_manager.py
from gi.repository import Gio, GLib


class FileManager:
    def __init__(self):
        pass

    def load_file_async(self, file: Gio.File, callback):
        """Asynchronously loads the content of a file."""
        file.load_contents_async(None, callback)

    def load_file_finish(self, file: Gio.File, result):
        """Finishes the asynchronous file load operation."""
        try:
            success, contents, etag = file.load_contents_finish(result)
            if success:
                # Decode the bytes to a string
                text = contents.decode("utf-8")
                return True, text
            return False, "Failed to load file contents."
        except GLib.Error as e:
            return False, e.message
        except UnicodeError:
            return False, "Invalid text encoding."

    def save_file_async(self, file: Gio.File, text: str, callback):
        """Asynchronously saves the given text content to a file."""
        bytes_content = GLib.Bytes.new(text.encode("utf-8"))
        file.replace_contents_bytes_async(
            bytes_content, None, False, Gio.FileCreateFlags.NONE, None, callback
        )

    def save_file_finish(self, file: Gio.File, result):
        """Finishes the asynchronous file save operation."""
        try:
            file.replace_contents_finish(result)
            return True, "File saved successfully."
        except GLib.Error as e:
            return False, e.message

    def get_file_type(self, file: Gio.File):
        """Returns the file type of a Gio.File."""
        try:
            file_info = file.query_info(
                "standard::type", Gio.FileQueryInfoFlags.NONE, None
            )
            return file_info.get_file_type()
        except GLib.Error:
            return Gio.FileType.UNKNOWN
