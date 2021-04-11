import math

from utils import center_and_shorten_str


class SSHColors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    LIGHTGRAY = "\033[90m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BACKBLUE = "\033[44m"
    BACKRED = "\033[41m"
    EOL = "\033[0m\n"


class SSHTemplate:
    """
    Return strings ready to be returned to the user.
    All functions return (outstring, nb_line_taken)
    """

    def __init__(self, term_width, term_height, nb_img_per_row):
        self.term_height = term_height
        self.term_width = term_width
        self.nb_img_per_row = nb_img_per_row

    def header(self):
        """
        Return the nice blue header at the top + offset
        """
        outstr = SSHColors.BACKBLUE + " " * self.term_width + SSHColors.ENDC
        outstr += (
            SSHColors.BACKBLUE
            + SSHColors.BOLD
            + self._line_center("ssh.signalstickers.com")
            + SSHColors.ENDC
        )
        outstr += SSHColors.BACKBLUE + " " * self.term_width + SSHColors.ENDC
        outstr += self._line()
        outstr += self._line()

        return outstr, 5

    def intro(self):
        """
        Return the few lines of intro + offset
        """
        outstr = self._line_center(
            "Welcome to Signal Stickers, the unofficial directory for Signal sticker packs."
        )
        outstr += self._line_center(
            "Follow https://twitter.com/signalstickers to stay tuned for new packs!"
        )
        outstr += self._line_center("Press h for help.")
        outstr += self._line()
        outstr += self._line()

        return outstr, 5

    def searched_terms(self, term):
        """
        Return the text when the user searches a word + offset
        """
        results_txt = f"Results for {SSHColors.BOLD}{term}{SSHColors.ENDC}"
        outstr = self._line_center("-" * 30)
        # Account for bold chars
        outstr += self._line(f"{results_txt:^{self.term_width+7}}")
        outstr += self._line()
        outstr += self._line_center("(press Esc to exit Search mode)")
        outstr += self._line()
        outstr += self._line()
        return outstr, 6

    def help(self):
        """
        Return the help content + offset
        """
        outstr = self._line()
        outstr += self._line_center_bold("HELP")
        outstr += self._line()
        outstr += self._line_bold("Navigation")
        outstr += self._line(
            "Use arrows or wasd to navigate around packs. Hit Return to select a pack."
        )
        outstr += self._line("To get back to pack list, press Esc.")
        outstr += self._line("To exit, use Ctrl+C or close the window.")
        outstr += self._line()
        outstr += self._line_bold("Search")
        outstr += self._line(
            "To search for a pack, use the / key, type your word, then press Return."
        )
        outstr += self._line('To exit "Search mode", press the Esc key.')
        outstr += self._line()
        outstr += self._line_bold("About signalstickers")
        outstr += self._line(
            "Signal Stickers is a community-organized, unofficial directory of sticker packs"
        )
        outstr += self._line(
            "for Signal, the secure messenger. All content on this server is copyrighted by their"
        )
        outstr += self._line(
            "respective owners. This server is not affiliated with Signal or Open Whisper Systems."
        )
        outstr += self._line()
        outstr += self._line_bold("About this project")
        outstr += self._line("This project is open source, under GPLv3.")
        outstr += self._line("For more information, or to report an issue, see")
        outstr += self._line("https://github.com/signalstickers/ssh-signalstickers")
        outstr += self._line()
        outstr += self._line_bold("Credits")
        outstr += self._line("2021 - Romain RICARD https://github.com/romainricard")
        outstr += self._line()
        outstr += self._line()
        outstr += self._line()
        outstr += self._line_center_bold("Press Esc to go back to pack list.")

        return outstr, 28

    def pad(self, offset):
        """
        Return padding at the bottom of the page
        """
        # return (
        #     "\n".join([str(i) for i in range((self.term_height - offset))]) + "\n"
        # )  # Use this for padding debug
        return "\n" * (self.term_height - offset)

    def make_thumbnails_row(self, thumbnails, height=12):
        """
        Take a list of thumbnails and concatenate them into a row
        A thumbnail is a 12*n (h*w) string in case of pack cover,
        or 10*n in case of pack details
        """

        thumbs_splitted = [t.splitlines() for t in thumbnails]

        thumbs_row = ""

        for i in range(0, height):
            char_row = ""

            for t in thumbs_splitted:
                char_row += f"  {t[i]}  "
            thumbs_row += char_row + "\n"

        return thumbs_row

    def details(self, pack):

        outstr = self._line(center_and_shorten_str(pack["title"], self.term_width))
        outstr += self._line(center_and_shorten_str(pack["author"], self.term_width))

        outstr += self._line()
        outstr += self._line(
            "To add this pack to Signal, Ctrl+click (or Alt+click) the following link:"
        )
        outstr += self._line(
            f"{SSHColors.LIGHTGRAY}https://signal.art/addstickers/#pack_id={pack['id']}&pack_key={pack['key']}{SSHColors.ENDC}"
        )
        outstr += self._line()
        outstr += self._line_key_val("Author", pack["author"])

        if pack.get("source"):
            outstr += self._line_key_val("Source", pack["source"])

        outstr += self._line_key_val(
            "NSFW",
            f"{SSHColors.WARNING}Yes{SSHColors.ENDC}" if pack.get("nsfw") else "No",
        )
        outstr += self._line_key_val(
            "Animated",
            f"{SSHColors.GREEN}Yes{SSHColors.ENDC}" if pack.get("animated") else "No",
        )
        outstr += self._line_key_val(
            "Original",
            f"{SSHColors.GREEN}Yes{SSHColors.ENDC}" if pack.get("original") else "No",
        )

        if pack.get("tags"):
            outstr += self._line_key_val("Tags", ", ".join(pack["tags"]))

        outstr += self._line()
        outstr += self._line()
        outstr += self._line("Preview of the first stickers:")
        outstr += self._line()

        offset = outstr.count("\n")
        # If the term width is not large enouth, the signal.art link will take 2 lines
        # Doing it for multiple lines is probably overkill, as at a small term width,
        # this prog will break in multiple parts anyway
        if self.term_width < 146:
            offset += math.ceil(146 / self.term_width) - 1

        return outstr, offset

    @staticmethod
    def create_thumbnail(
        image, title="", selected=False, original=False, animated=False, nsfw=False
    ):
        """
        Images must be 15px wide
        """
        max_img_width = 15
        color = (
            f"{SSHColors.GREEN}{SSHColors.BOLD}" if selected else SSHColors.LIGHTGRAY
        )

        border_h = f"{color}+{'-' * max_img_width}+{SSHColors.ENDC}\n"

        img_bordered = border_h

        if nsfw:
            # Replace image with warning
            image = (
                f"{' '*15}\n" * 3
                + SSHColors.LIGHTGRAY
                + f"{'This pack is':^15}\n"
                + SSHColors.LIGHTGRAY
                + f"{'NSFW':^15}\n"
                + f"{' '*15}\n" * 3
            )

        for img_line in image.splitlines():
            img_bordered += (
                f"{color}|{SSHColors.ENDC}{img_line}{color}|{SSHColors.ENDC}\n"
            )

        img_bordered += border_h

        if original:
            label = f"{SSHColors.BACKBLUE}Original{SSHColors.ENDC}"
            start_pos = 31 if selected else 27
            end_pos = 52 if selected else 44
            img_bordered = img_bordered[:start_pos] + label + img_bordered[end_pos:]

        if animated:
            label = f"{SSHColors.BACKRED}Animated{SSHColors.ENDC}"
            start_pos = 93 if selected and original else 97 if selected else 81
            end_pos = 114 if selected and original else 118 if selected else 94
            img_bordered = img_bordered[:start_pos] + label + img_bordered[end_pos:]

        if title:

            pack_title = (
                f"{color}|{SSHColors.ENDC}"
                + center_and_shorten_str(title, 15, "…")
                + f"{color}|{SSHColors.ENDC}\n"
            )

            img_bordered += pack_title
            img_bordered += border_h

        return img_bordered

    # Utils

    def _line(self, content=""):
        return f"{content}\n"

    def _line_center(self, content=""):
        return self._line(f"{content:^{self.term_width}}")

    def _line_bold(self, content=""):
        return self._line(f"{SSHColors.BOLD}{content}{SSHColors.ENDC}")

    def _line_center_bold(self, content=""):
        return self._line(
            f"{SSHColors.BOLD}{content:^{self.term_width}}{SSHColors.ENDC}"
        )

    def _line_key_val(self, key="", val=""):
        return self._line(f"{SSHColors.BOLD}{key:10}{SSHColors.ENDC} {val}")

    @staticmethod
    def banner(password):
        return f"""

        +--------------------------------+
        | To prove that you are not a    |
        | robot, select all squares with |
        |                                |
        |  TRAFFIC LIGHTS                |
        |                                |
        |  (///%**%  %%/&&@&&  %(##*,((  |
        |  ((///*//  &##@%&&@  &##/,**(  |
        |  ((/%*/*%  &#&/#//&  %#(&((#*  |
        |                                |
        |  ((/(/*/%  %#&#(((#  #/#%*(,/  |
        |  (/(&///&  &/&%//%#  #/#(///*  |
        |  (//%(//&  #%%#%%&,  ,%,*////  |
        |                                |
        |  ((%#(((&  *#,/&*&*  #*,/////  |
        |  /&%#(((%  **,*&/**  /(,*/(./  |
        |  /(,.&(((  **#/***#  %%**////  |
        +--------------------------------+


Just kidding, just use the following password
to enter this "website":

            {password}

"""
