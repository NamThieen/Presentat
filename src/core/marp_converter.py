# src/core/marp_converter.py
import subprocess
import shutil


class MarpConverter:
    def __init__(self):
        self.marp_path = shutil.which("marp")
        if not self.marp_path:
            raise RuntimeError(
                "Marp CLI not found. Please ensure it's on the PATH.")

    def convert_to_html(self, markdown_content: str, base_dir=None):
        """
        Converts markdown content to HTML using Marp CLI.
        This is a synchronous (blocking) function.
        """
        try:
            command = [self.marp_path, "--html", "--allow-local-files", "-"]

            if base_dir:
                command.extend(["--input-dir", base_dir])
            result = subprocess.run(
                command,
                input=markdown_content.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            html_content = result.stdout.decode("utf-8")
            return True, html_content

        except subprocess.CalledProcessError as e:
            error_message = f"Marp CLI conversion failed with exit code: {
                e.returncode
            }\n{e.stderr.decode('utf-8')}"
            return False, error_message
        except FileNotFoundError:
            return (
                False,
                "Marp CLI was not found. Please ensure it's installed.",
            )
        except Exception as e:
            return False, f"An unexpected error occurred: {e}"
