import json
import random
import unicodedata
import zipfile


def get_random_password():
    return random.choice([
        "potato",
        "circus",
        "kitchen",
        "signal",
        "sticker",
        "kitten",
        "python",
        "bubble",
        "sequoia",
        "doggo",
        "frenchfries",
        "montpellier"
    ]) + str(random.randrange(1, 100))


class PacksDB:
    def __init__(self, zip_path):
        self.f_zip = zipfile.ZipFile(zip_path)
        self.index = self.get("packsinfo")

    def get(self, id):
        with self.f_zip.open(f"{id}.json") as f_in:
            return json.load(f_in)


class Pager:

    def __init__(self, page_size, packsdb_inst):
        self._packsdb = packsdb_inst
        self.page_size = page_size
        self._all_packs_paginated = [self._packsdb.index[i:i+self.page_size]
                                     for i in range(0, len(self._packsdb.index), self.page_size)]

        # This contains the list of all packs for the current mode (all or search mode)
        self._packs = self._all_packs_paginated

        # Values depending on the current page
        self.page_idx = 0
        self._cur_page = None
        self._cur_page_len = None
        self._update_page()

        self.search_mode = False

    def details(self, pack):
        # For now, only show 1st page of stickers
        self._packs = pack["thumbs"][:self.page_size]
        # Do not call _update_page(), as this would mess up with page.idx
        self._cur_page = self._packs 
        self._cur_page_len = len(self._cur_page)

    def exit_details(self):
        """
        Exit details mode
        """
        self._packs = self._all_packs_paginated
        self._update_page()

    def search(self, term):
        self.search_mode = True
        term = term.lower().lstrip()
        matching_packs = []
        for pack in self._packsdb.index:
            if term in pack["title"].lower() or term in pack.get("tags", ""):
                matching_packs.append(pack)

        self._packs = [matching_packs[i:i+self.page_size]
                       for i in range(0, len(matching_packs), self.page_size)]
        self.page_idx = 0
        self._update_page()


    def exit_search(self):
        """
        Exit search mode
        """
        self.search_mode = False
        self._packs = self._all_packs_paginated
        self.page_idx = 0
        self._update_page()

    def _update_page(self):
        """
        Update internal data with the current `page_idx`
        """
        self._cur_page = self._packs[self.page_idx] if self._packs else [
        ]  # in case of empty results
        self._cur_page_len = len(self._cur_page)

    def next(self):
        if self.has_next:
            self.page_idx += 1
            self._update_page()

    def prev(self):
        if self.has_prev:
            self.page_idx -= 1
            self._update_page()

    @property
    def has_next(self):
        return self.page_idx < len(self._packs) - 1

    @property
    def has_prev(self):
        return self.page_idx > 0

    def __len__(self):
        """
        Return the length of the current page
        """
        return self._cur_page_len

    @property
    def content(self):
        """
        Return content for the current page
        """
        return self._cur_page


def center_and_shorten_str(string, width, placeholder="…"):
    """
    Center (and shorten if applicable) a string, handling CJK characters
    Inspired by https://medium.com/@gullevek/python-output-formatting-double-byte-characters-6d6d18d04be3
    """

    def str_length(string):
        """
        Return the len of a str, including double count for double width characters
        """
        return sum(1 + (unicodedata.east_asian_width(c) in "WF") for c in string)

    string_len_cjk = str_length(str(string))

    if string_len_cjk > width:
        cur_len = 0
        out_string = ''
        for char in str(string):
            cur_len += 2 if unicodedata.east_asian_width(char) in "WF" else 1
            if cur_len <= (width - len(placeholder)):
                out_string += char
        return f"{out_string}{placeholder}"
    else:
        # Center the str, taking the actual width into account
        align_width = width - (string_len_cjk-len(string))
        return f'{string:^{align_width}}'
