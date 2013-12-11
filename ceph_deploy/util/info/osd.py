"""
A class for helping to report osd details.
"""
import re


class osd_info:


    def __init__(self):
        self.whomai = None
        self.magic = None
        self.active = None
        self.datapath = None
        self.datapathtyp = None
        self.realdatapath = None
        self.journalpath = None
        self.realjournalpath = None


    def valid_whoami(self):
        # are we a sensible number for an osd?
        if (self.whoami).isdigit():
            return True
        else:
            return False


    def valid_datapath(self):
        # does our osd number match our directory link?
        if re.match(self.whoami, ''.join(reversed(self.datapath))):
            return True
        else:
            return False


    def valid_journal(self):
        # did we find a journal
        if self.journalpath and self.realjournalpath:
            return True
        else:
            return False
