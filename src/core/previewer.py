# previewer.py
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
# MERCHANTABILITY and FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Gio, GLib, WebKit
import gi
gi.require_version("WebKit", "6.0")


class PresentationPreviewer(WebKit.WebView):
    __gtype_name__ = "PresentationPreviewer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.get_settings().set_enable_developer_extras(True)
        self.get_settings().set_enable_javascript(True)
        self.get_settings().set_enable_media(False)

        web_context = WebKit.WebContext.get_default()

        web_context.register_uri_scheme(
            "marp",
            self._on_uri_scheme_request,
            None,
        )

    def _on_uri_scheme_request(self, request: WebKit.URISchemeRequest, user_data=None):
        uri = request.get_uri()
        if uri.startswith("marp://preview"):
            stream = Gio.MemoryInputStream.new_from_data(b"")
            request.finish(stream, 0, None)
        else:
            error = GLib.Error(
                WebKit.URI_SCHEME_ERROR,
                WebKit.URI_SCHEME_ERROR.FAILED,
                f"Unsupported URI: {uri}",
            )
            request.finish_error(error)

    def load_marp_html(self, html_content):
        self.load_html(html_content, "marp://preview/")
