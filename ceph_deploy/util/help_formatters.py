import argparse


class ToggleRawTextHelpFormatter(argparse.HelpFormatter):
    """ArgParse help formatter that allows raw text in individual help strings

        Inspired by the SmartFormatter at
           https://bitbucket.org/ruamel/std.argparse

       Normally to include newlines in the help output of argparse, you have
       use argparse.RawDescriptionHelpFormatter. But this means raw text is enabled
       everywhere, and not just for specific help entries where you might need it.

       This help formatter allows for you to optional enable/toggle raw text on
       individual menu items by prefixing the help string with 'R|'.

       Example:

       parser.formatter_class = ToggleRawTextHelpFormatter
       parser.add_argument('--verbose', action=store_true,
                           help='Enable verbose mode')
       #Above help is formatted just as default argparse.HelpFormatter

       parser.add_argument('--complex-arg', action=store_true,
                           help=('R|This help description use '
                                 'newlines and tabs and they will be preserved in'
                                 'the help output.\n\n'
                                 '\tHow cool is that?'))
    """
    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()  
        return argparse.HelpFormatter._split_lines(self, text, width)
