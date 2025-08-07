# window.py
#
# Copyright 2025 nam
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later
from threading import Thread
from .core.previewer import PresentationPreviewer
from .core.marp_converter import MarpConverter
from .core.directory_tree import create_child_model_func, FileListItem
from .core.file_manager import FileManager
from gi.repository import Adw, Gtk, Gio, GLib
import re
from urllib.parse import urlparse


@Gtk.Template(resource_path="/app/nam/Presentat/window.ui")
class PresentatWindow(Adw.ApplicationWindow):
    __gtype_name__ = "PresentatWindow"
    main_text_view = Gtk.Template.Child()
    cursor_pos = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    action_menu = Gtk.Template.Child()

    preview_container = Gtk.Template.Child()
    split_view = Gtk.Template.Child()
    marp_converter = None
    show_sidebar_button = Gtk.Template.Child()

    directory_list_view = Gtk.Template.Child()
    preview_web_view = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.preview_web_view = PresentationPreviewer()
        self.preview_container.set_child(self.preview_web_view)

        self.file_manager = FileManager()
        self.sidebar_expanded_position = 300
        open_action = Gio.SimpleAction(name="open-file")
        open_action.connect("activate", self.open_file_dialog)
        self.add_action(open_action)

        save_action = Gio.SimpleAction(name="save-as")
        save_action.connect("activate", self.save_file_dialog)
        self.add_action(save_action)

        # Action for opening a folder
        open_folder_action = Gio.SimpleAction(name="open-folder")
        open_folder_action.connect("activate", self.open_folder_dialog)
        self.add_action(open_folder_action)

        buffer = self.main_text_view.get_buffer()
        buffer.connect("notify::cursor-position", self.update_cursor_position)

        self.root_list_store = Gio.ListStore.new(FileListItem)
        self.tree_list_model = Gtk.TreeListModel.new(
            self.root_list_store, False, False, create_child_model_func
        )

        selection_model = Gtk.SingleSelection(model=self.tree_list_model)
        self.directory_list_view.set_model(selection_model)
        factory = self.directory_list_view.get_factory()
        if isinstance(factory, Gtk.SignalListItemFactory):
            factory.connect("setup", self._factory_setup)
            factory.connect("bind", self._factory_bind)

        selection_model.connect("notify::selected-item",
                                self.on_list_item_selected)

        self.current_folder = None
        self._current_file = None
        self._preview_update_timeout_id = None
        self.marp_converter = MarpConverter()
        buffer.connect("changed", self.on_text_changed)

    def on_text_changed(self, buffer):
        if self._preview_update_timeout_id is not None:
            GLib.source_remove(self._preview_update_timeout_id)

        self._preview_update_timeout_id = GLib.timeout_add_seconds(
            0.5, self._trigger_marp_conversion
        )

    def _trigger_marp_conversion(self):
        self._preview_update_timeout_id = None
        markdown_text = self.main_text_view.get_buffer().get_text(
            self.main_text_view.get_buffer().get_start_iter(),
            self.main_text_view.get_buffer().get_end_iter(),
            False,
        )
        if self._current_file:
            try:
                current_dir = self._current_file.get_parent().get_path()

                pattern = re.compile(r"\!\[.*?\]\((.*?)\)")

                def replace_uri(match):
                    original_path = match.group(1)
                    parsed_uri = urlparse(original_path)
                    if parsed_uri.scheme in ["http", "https", "file"]:
                        return match.group(0)
                    full_path = GLib.build_filenamev(
                        [current_dir, original_path])

                    # Convert the local path to a file URI
                    file_uri = Gio.File.new_for_path(full_path).get_uri()

                    # Return the modified Markdown string with the new URI
                    return match.group(0).replace(original_path, file_uri)

                modified_markdown_text = pattern.sub(
                    replace_uri, markdown_text)

            except Exception as e:
                # Fallback to the original text if path conversion fails
                print(f"Error during image path conversion: {e}")
                modified_markdown_text = markdown_text
        else:
            modified_markdown_text = markdown_text

        # We need to run the blocking conversion in a separate thread
        conversion_thread = Thread(
            target=self._run_conversion, args=(modified_markdown_text,)
        )
        conversion_thread.start()

        return False  # Required for GLib timeout

    def _run_conversion(self, markdown_content):
        """Runs the blocking conversion in a background thread."""
        success, result = self.marp_converter.convert_to_html(markdown_content)

        # Use GLib.idle_add to update the UI from the main thread
        GLib.idle_add(self._on_marp_html_received, success, result)

    def _on_marp_html_received(self, success, result):
        if success:
            self.preview_web_view.load_marp_html(result)
            # You can add a toast here for success if you wish
        else:
            error_html = f"<html><body><h1>Error</h1><p>{
                GLib.markup_escape_text(result)
            }</p></body></html>"
            self.preview_web_view.load_marp_html(error_html)
            self.toast_overlay.add_toast(Adw.Toast(title="Conversion failed"))

    def _factory_setup(self, factory, list_item: Gtk.ListItem):
        """
        Sets up the widgets for each list item, including the TreeExpander.
        """
        expander = Gtk.TreeExpander.new()

        # Container for the icon and label
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image()
        label = Gtk.Label(xalign=0.0)
        box.append(icon)
        box.append(label)

        expander.set_child(box)
        list_item.set_child(expander)

    def _factory_bind(self, factory, list_item: Gtk.ListItem):
        tree_list_row: Gtk.TreeListRow = list_item.get_item()
        item: FileListItem = tree_list_row.get_item()
        expander: Gtk.TreeExpander = list_item.get_child()
        box: Gtk.Box = expander.get_child()
        icon: Gtk.Image = box.get_first_child()
        label: Gtk.Label = box.get_last_child()

        expander.set_list_row(tree_list_row)

        label.set_text(item.display_name)

        try:
            file_info = item.file.query_info(
                "standard::icon", Gio.FileQueryInfoFlags.NONE, None
            )
            gicon = file_info.get_icon()
        except GLib.Error:
            gicon = Gio.Icon.new_for_string("text-x-generic-symbolic")

        if item.is_dir:
            gicon = Gio.Icon.new_for_string("folder-symbolic")

        icon.set_from_gicon(gicon)

    def on_list_item_selected(self, selection_model: Gtk.SingleSelection, pspec):
        selected_row: Gtk.TreeListRow = selection_model.get_selected_item()
        if not selected_row:
            return

        # Corrected: Get the FileListItem from the TreeListRow
        selected_item: FileListItem = selected_row.get_item()

        if selected_item.is_dir:
            # If it's a directory, toggle its expanded state.
            selected_row.set_expanded(not selected_row.get_expanded())
        else:
            # If it's a file, open it.
            self.open_file(selected_item.file)

    # Cursor stuff
    def update_cursor_position(self, buffer, _):
        cursor_pos = buffer.props.cursor_position
        iter = buffer.get_iter_at_offset(cursor_pos)
        line = iter.get_line() + 1
        column = iter.get_line_offset() + 1
        self.cursor_pos.set_text(f"Ln {line}, Col {column}")

    # Save file stuff
    def save_file_dialog(self, action, _):
        native = Gtk.FileDialog()
        native.save(self, None, self.on_save_response)

    def on_save_response(self, dialog, result):
        try:
            file = dialog.save_finish(result)
            if file is not None:
                self.save_file(file)
        except GLib.Error as e:
            self.toast_overlay.add_toast(
                Adw.Toast(title=f"Error saving file: {e.message}")
            )

    def save_file(self, file):
        buffer = self.main_text_view.get_buffer()
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        text = buffer.get_text(start, end, False)
        if not text:
            return
        self.file_manager.save_file_async(file, text, self._on_file_saved)

    def _on_file_saved(self, file, result):
        success, message = self.file_manager.save_file_finish(file, result)
        if success:
            display_name = file.get_basename()
            self.toast_overlay.add_toast(
                Adw.Toast(title=f"Saved as {display_name}"))
        else:
            self.toast_overlay.add_toast(
                Adw.Toast(title=f"Error saving file: {message}")
            )

    # Open file stuff (existing)
    def open_file_dialog(self, action, _):
        native = Gtk.FileDialog()
        native.open(self, None, self.on_open_response)

    def on_open_response(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file is not None:
                self.open_file(file)
        except GLib.Error as e:
            self.toast_overlay.add_toast(
                Adw.Toast(title=f"Error opening file: {e.message}")
            )

    def open_file(self, file):
        if self.file_manager.get_file_type(file) == Gio.FileType.DIRECTORY:
            self.toast_overlay.add_toast(
                Adw.Toast(title="Cannot open directory as a file.")
            )
            return
        self.file_manager.load_file_async(file, self._on_file_loaded)

    def _on_file_loaded(self, file, result):
        success, content = self.file_manager.load_file_finish(file, result)
        if success:
            self._current_file = file
            display_name = file.get_basename()
            buffer = self.main_text_view.get_buffer()
            buffer.set_text(content)
            buffer.place_cursor(buffer.get_start_iter())
            self.set_title(display_name)
            self.toast_overlay.add_toast(
                Adw.Toast(title=f"Opened {display_name}"))
        else:
            self._current_file = None
            self.toast_overlay.add_toast(
                Adw.Toast(title=f"Unable to open file: {content}")
            )

    # Open folder dialog
    def open_folder_dialog(self, action, _):
        native = Gtk.FileDialog()
        native.select_folder(self, None, self.on_open_folder_response)

    def on_open_folder_response(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder is not None:
                self.current_folder = folder
                self.populate_directory_tree(folder)
                self.set_title(f"Text-viewer - {folder.get_basename()}")
                self.toast_overlay.add_toast(
                    Adw.Toast(title=f"Opened folder: {folder.get_basename()}")
                )
            else:
                self.toast_overlay.add_toast(
                    Adw.Toast(title="No folder selected."))
        except GLib.Error as e:
            self.toast_overlay.add_toast(
                Adw.Toast(title=f"Error opening folder: {e.message}")
            )

    def populate_directory_tree(self, folder: Gio.File):
        """
        Populates the Gtk.TreeListModel with the root folder.
        The children will be populated on-demand.
        """
        self.root_list_store.remove_all()
        root_item = FileListItem(file=folder)
        self.root_list_store.append(root_item)

        root_row = self.tree_list_model.get_row(0)
        if root_row:
            root_row.set_expanded(True)
