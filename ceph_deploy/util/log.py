import logging

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': RED,
    'ERROR': RED
}

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

BASE_COLOR_FORMAT = "[$BOLD%(name)s$RESET][%(color_levelname)-17s] %(message)s"
BASE_FORMAT = "%(asctime)s [%(name)s][%(levelname)-6s] %(message)s"


def color_message(message):
    message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    return message


class ColoredFormatter(logging.Formatter):
    """
    A very basic logging formatter that not only applies color to the levels of
    the ouput but will also truncate the level names so that they do not alter
    the visuals of logging when presented on the terminal.
    """

    def __init__(self, msg):
        logging.Formatter.__init__(self, msg)

    def format(self, record):
        levelname = record.levelname
        truncated_level = record.levelname[:6]
        if levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + truncated_level + RESET_SEQ
            record.color_levelname = levelname_color
        return logging.Formatter.format(self, record)


def color_format():
    """
    Main entry point to get a colored formatter, it will use the
    BASE_FORMAT by default.
    """
    color_format = color_message(BASE_COLOR_FORMAT)
    return ColoredFormatter(color_format)
