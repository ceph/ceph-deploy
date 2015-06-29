import argparse


class ToggleRawTextHelpFormatter(argparse.HelpFormatter):
    """Inspired by the SmartFormatter at
       https://bitbucket.org/ruamel/std.argparse
   """
    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()  
        return argparse.HelpFormatter._split_lines(self, text, width)
