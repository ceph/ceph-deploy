"""
A class for helping to report osd details.
"""
import re


class OSDInfo(object):


    def __init__(self):
        self.whoami = None
        self.magic = None
        self.active = None
        self.datapath = None
        self.datapathtyp = None
        self.realdatapath = None
        self.journalpath = None
        self.realjournalpath = None


    def valid_whoami(self):
        # are we a sensible number for an osd?
        if self.whoami.isdigit():
            return True
        return False


    def valid_datapath(self):
        # does our osd number match our directory link?
        if re.match(''.join(reversed(self.whoami)), ''.join(reversed(self.datapath))):
            return True
        return False


    def valid_journal(self):
        # did we find a journal?
        if self.journalpath and self.realjournalpath:
            return True
        return False
