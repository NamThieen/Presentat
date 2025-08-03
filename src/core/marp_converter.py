# src/core/marp_converter.py
import subprocess
import shutil
import tempfile
import os
from gi.repository import GLib, Gio

class MarpConverter:
    def __init__(self):
        self.marp_path = "/app/bin/marp"

    def convert_to_html_async(self, markdown_content: str, callback):
        try:
            # The command now starts with 'node', followed by the marp script path
            command = [self.node_path, self.marp_path, "--html", "-"]

            # Spawn the process with pipes for stdin, stdout, and stderr
            success, pid, stdin, stdout, stderr = GLib.spawn_async_with_pipes(
                None,
                command,
                None,
                GLib.SpawnFlags.SEARCH_PATH | GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
            )

            if not success:
                callback(False, "Failed to spawn Marp CLI process.")
                return

            gio_stdin = Gio.UnixOutputStream.new(stdin.get_fd(), True)
            gio_stdout = Gio.UnixInputStream.new(stdout.get_fd(), True)
            gio_stderr = Gio.UnixInputStream.new(stderr.get_fd(), True)

            gio_stdin.write_bytes(GLib.Bytes.new(markdown_content.encode('utf-8')), None)
            gio_stdin.close(None)

            output_stream = Gio.DataInputStream.new(gio_stdout)

            GLib.child_watch_add(
                GLib.PRIORITY_DEFAULT,
                pid,
                lambda pid, status, user_data: self._on_marp_finished_with_pipes(pid, status, user_data),
                (output_stream, gio_stderr, callback)
            )

        except Exception as e:
            callback(False, f"An unexpected error occurred: {e}")

    def _on_marp_finished_with_pipes(self, pid, status, data):
        output_stream, stderr_stream, callback = data

        try:
            if status == 0:
                html_content = output_stream.read_all(None)[0].decode('utf-8')
                callback(True, html_content)
            else:
                stderr_content = stderr_stream.read_all(None)[0].decode('utf-8')
                print(f"Marp CLI exited with code: {status}, stderr: {stderr_content}")
                callback(False, f"Marp CLI conversion failed: {stderr_content}")
        except Exception as e:
            callback(False, f"Error processing Marp output: {e}")
        finally:
            output_stream.close(None)
            stderr_stream.close(None)
            GLib.spawn_close_pid(pid)
