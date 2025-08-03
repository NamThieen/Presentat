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

import gi
gi.require_version('WebKit', '6.0')
from gi.repository import Gio, GLib, GObject, WebKit

class PresentationPreviewer(WebKit.WebView):
    """
    A custom WebKitWebView to handle Marp previews and inter-process communication.
    """
    __gtype_name__ = 'PresentationPreviewer'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.get_settings().set_enable_developer_extras(True)
        self.get_settings().set_enable_javascript(True)
        self.get_settings().set_enable_media(False)

        # Get the default WebKit.WebContext.
        # It's a shared singleton for all web views.
        web_context = WebKit.WebContext.get_default()

        # The correct way to handle a custom URI scheme is to register a handler
        # on the WebContext. We do NOT connect a signal on the WebView instance.
        web_context.register_uri_scheme(
            "marp",
            self._on_uri_scheme_request, # Corrected to use the existing method name
            None
        )

    def _on_uri_scheme_request(self, request: WebKit.URISchemeRequest):
        """
        This is the handler for custom 'marp://' URIs.
        It is called by the WebKit.WebContext whenever a matching URI is
        requested by this or any other WebKitWebView in the application.
        """
        uri = request.get_uri()
        if uri.startswith("marp://preview"):
            # Acknowledging the request, even if we are not providing content here.
            # load_html() is already taking care of the content, but the scheme
            # handler is still required for the load to succeed.
            stream = Gio.MemoryInputStream.new_from_data(b"", -1, None)
            request.finish(stream, 0, None)
        else:
            error = GLib.Error(
                WebKit.URI_SCHEME_ERROR,
                WebKit.URI_SCHEME_ERROR.FAILED,
                f"Unsupported URI: {uri}"
            )
            request.finish_error(error)

    def load_marp_html(self, html_content):
        """
        Loads the generated HTML content directly into the web view.
        The custom URI 'marp://preview/' tells our handler to handle the request.
        """
        self.load_html(html_content, 'marp://preview/')
