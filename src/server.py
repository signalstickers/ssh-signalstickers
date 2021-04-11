import asyncio
import crypt
import getpass
import json
import logging
import os
import string
import sys
import zipfile

import asyncssh

from templates import SSHColors, SSHTemplate
from utils import PacksDB, Pager, get_random_password

printable = string.ascii_letters + string.digits + string.punctuation + " "


logging.basicConfig(
    filename="sshserver.log",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)

asyncssh.set_log_level("WARNING")

PACKSDB = PacksDB("packs.zip")

key_actions = {
    # Up
    "\x1b[A": "up",
    "z": "up",
    "w": "up",
    # Down
    "\x1b[B": "down",
    "s": "down",
    # Right
    "\x1b[C": "right",
    "d": "right",
    # Left
    "\x1b[D": "left",
    "q": "left",
    "a": "left",
    # Controls
    "/": "search",
    "h": "help",
    "\x1b": "escape",
    "\x0d": "return",
    "\x03": "exit",
    "\x04": "exit",
    "\x1a": "exit",
}


def log(message, conn_info):
    logging.info("[%s] %s", conn_info.get_extra_info("peername")[0], message)


class MySSHSession(asyncssh.SSHServerSession):
    def __init__(
        self,
    ):
        super().__init__()
        self._chan = None

        # Navigation
        self.cursor_pack = (
            0  # Hold the current pack hilighted by the cursor, relative to the page
        )
        self.nb_packs_per_row = 0
        self.pagination_offset = 0

        # Help page have to be displayed
        self.show_help = False

        # Pack details have to be displayed
        # This will use the pack index stored in self.cursor_pack
        self.show_pack_details = False

        # The Pager for this client
        self.pager = None

        # If search mode is set, typed chars are displayed
        self.search_mode = None
        # Hold the term searched by the user
        self.search_term = None

        # Client info
        self.term_height = None
        self.term_width = None
        self.pack_viewed = 0

        # If False, the app has just launched. Else, we can safely clear
        # it while writing to stdout
        self.can_clear_term = False

    def connection_made(self, chan):
        self._chan = chan

    def session_started(self):
        self.term_width, self.term_height, _, _ = self._chan.get_terminal_size()

        self.nb_packs_per_row = int(self.term_width / 21)

        self.template = SSHTemplate(
            term_width=self.term_width,
            term_height=self.term_height,
            nb_img_per_row=self.nb_packs_per_row,
        )

        # A thumbnails with name takes 13 lines
        # 10 is hardcoded (size of SSHTemplate.header + SSHTemplate.intro)
        page_size = int((self.term_height - 10) / 13) * self.nb_packs_per_row
        self.pager = Pager(page_size=page_size, packsdb_inst=PACKSDB)

        self._unset_search_mode()
        self.render()
        log("Sessions started", self._chan)

    def clear_screen(self):
        """
        Clear term content and put the cursor to top left
        """
        # Clear screen
        self._chan.write("\033[1J")
        # Move cursor to top left
        self._chan.write("\033[1;1H")

    def render(self):
        def _write(content):
            """
            Write `content` to client stdout
            """

            if self.can_clear_term:
                self.clear_screen()
            else:
                self.can_clear_term = True

            self.last_page_size = len(content)
            self._chan.write(content)

        offset = 0
        outstr = ""

        def _draw_packs():

            packs_str = ""
            packs_thumbs_list = []

            for idx, pack in enumerate(self.pager.content):
                packs_thumbs_list.append(
                    self.template.create_thumbnail(
                        pack["cover"],
                        title=pack["title"],
                        selected=idx == self.cursor_pack,
                        original=pack.get("original", False),
                        animated=pack.get("animated", False),
                        nsfw=pack.get("nsfw", False),
                    ),
                )

            for i in range(0, len(packs_thumbs_list), self.nb_packs_per_row):
                row = self.template.make_thumbnails_row(
                    packs_thumbs_list[i : i + self.nb_packs_per_row],
                    12,  # height of a thumb with title
                )
                packs_str += row
                packs_str += "\n"

            return packs_str, packs_str.count("\n")

        def _draw_pack_details_thumbs():
            thumbs_str = ""
            thumbs_list = []

            thumbs_list = [
                self.template.create_thumbnail(img) for img in self.pager.content
            ]

            for i in range(0, len(thumbs_list), self.nb_packs_per_row):
                row = self.template.make_thumbnails_row(
                    thumbs_list[i : i + self.nb_packs_per_row],
                    10,  # height of a thumb without title
                )
                thumbs_str += row
                thumbs_str += "\n"

            return thumbs_str, thumbs_str.count("\n")

        # Render header
        header, off_add = self.template.header()
        offset += off_add
        outstr += header

        # Render help page
        if self.show_help:
            help, off_add = self.template.help()
            offset += off_add
            outstr += help
            outstr += self.template.pad(offset)
            _write(outstr)
            return

        # Render pack details page
        if self.show_pack_details:
            pack = PACKSDB.get(self.pager.content[self.cursor_pack]["id"])
            details_rendered, off_add = self.template.details(pack=pack)
            outstr += details_rendered
            offset += off_add

            # Set the pager for this pack
            self.pager.details(pack)

            packs, off_add = _draw_pack_details_thumbs()
            outstr += packs
            offset += off_add

            outstr += self.template.pad(offset)
            _write(outstr)
            return

        # Render intro
        intro, off_add = self.template.intro()
        outstr += intro
        offset += off_add

        # Render searched term text
        if self.search_term:
            st, off_add = self.template.searched_terms(self.search_term)
            outstr += st
            offset += off_add
            if not self.pager.search_mode:
                # Initialize the page_size for
                self.pager.page_size = (
                    int((self.term_height - offset) / 13) * self.nb_packs_per_row
                )
                self.pager.search(term=self.search_term)

        packs, off_add = _draw_packs()
        outstr += packs
        offset += off_add

        # Add padding at the bottom if needed
        outstr += self.template.pad(offset)

        # Write rendered output
        _write(outstr)

    def _set_search_mode(self):
        self._chan.write(
            SSHColors.BOLD + "Search" + SSHColors.ENDC + " (press Return to validate): "
        )
        self._chan.set_echo(True)
        self._chan.set_line_mode(True)
        self.search_mode = True

    def _unset_search_mode(self):
        self._chan.set_echo(False)
        self._chan.set_line_mode(False)
        self.search_mode = False

    def shell_requested(self):
        return True

    def data_received(self, data, datatype):

        # Unknown command
        if data not in key_actions and not self.search_mode:
            return

        if self.search_mode:
            # Called after validation of the search.
            self.search_term = "".join(filter(lambda c: c in printable, data))
            self._unset_search_mode()
            self.cursor_pack = 0
            self.render()

            return

        if key_actions[data] == "exit":
            self.eof_received()

        if key_actions[data] == "escape":
            self._unset_search_mode()
            self.show_help = False

            if self.search_term:
                self.search_term = None
                self.cursor_pack = 0
                # Reset page size
                # A thumbnails with name takes 13 lines
                # 10 is hardcoded (size of SSHTemplate.header + SSHTemplate.intro)
                self.pager.page_size = (
                    int((self.term_height - 10) / 13) * self.nb_packs_per_row
                )
                self.pager.exit_search()

            if self.show_pack_details:
                self.show_pack_details = False
                self.pager.exit_details()

            self.render()
            return

        if key_actions[data] == "return":
            self.show_pack_details = True
            self.render()
            self.pack_viewed += 1  # for stats
            return

        if key_actions[data] == "help":
            self.show_help = True
            self.render()

        # Ignore actions bellow if in help page or pack details
        if self.show_help or self.show_pack_details:
            return

        if key_actions[data] == "right":
            if self.cursor_pack < len(self.pager) - 1:
                self.cursor_pack += 1
                self.render()
            elif self.pager.has_next:
                self.pager.next()
                self.cursor_pack = 0
                self.render()

        if key_actions[data] == "left":
            if self.cursor_pack == 0:
                if self.pager.has_prev:
                    self.pager.prev()
                    self.cursor_pack = len(self.pager) - 1
                    self.render()
            else:
                self.cursor_pack -= 1
                self.render()

        if key_actions[data] == "down":
            if self.cursor_pack + self.nb_packs_per_row < len(self.pager):
                self.cursor_pack += self.nb_packs_per_row
                self.render()
            elif self.pager.has_next:
                self.pager.next()
                self.cursor_pack = (
                    self.cursor_pack + self.nb_packs_per_row
                ) % self.nb_packs_per_row
                if self.cursor_pack >= len(self.pager):
                    self.cursor_pack = len(self.pager) - 1
                self.render()
            else:
                self.cursor_pack = len(self.pager) - 1
                self.render()

        if key_actions[data] == "up":

            if self.cursor_pack - self.nb_packs_per_row >= 0:
                self.cursor_pack -= self.nb_packs_per_row
                self.render()
            else:
                if self.pager.has_prev:
                    self.pager.prev()
                    self.cursor_pack = self.pager.page_size - (
                        self.nb_packs_per_row - self.cursor_pack
                    )
                    self.render()

        if key_actions[data] == "search":
            self._set_search_mode()
            return

    def eof_received(self):
        self.clear_screen()
        log(f"Client disconnected. {self.pack_viewed} pack viewed.", self._chan)
        self._chan.exit(0)

    def break_received(self, _):
        self.eof_received()

    def soft_eof_received(self):
        self.eof_received()


class MySSHServer(asyncssh.SSHServer):
    def connection_made(self, conn):
        self.conn = conn
        self.conn_pass = get_random_password()
        conn.send_auth_banner(SSHTemplate.banner(self.conn_pass))
        log(
            "SSH connection received",
            self.conn,
        )

    def connection_lost(self, exc):
        pass

    def password_auth_supported(self):
        return True

    def begin_auth(self, _):
        return True  # Set to False to disable authentication

    def validate_password(self, user, password):
        success = password.strip().lower() == self.conn_pass
        log(f"Login {'success' if success else 'failed'}", self.conn)
        return success

    def session_requested(self):
        return MySSHSession()


async def start_server():
    port = int(os.environ.get("SSH_SERVER_PORT", 8022))
    await asyncssh.create_server(
        MySSHServer, "", port, server_host_keys=["key"], line_editor=True
    )


loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(start_server())
except (OSError, asyncssh.Error) as exc:
    sys.exit("Error starting server: " + str(exc))

logging.info("Starting server as user %s", getpass.getuser())
loop.run_forever()
