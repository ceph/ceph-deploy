

class NormalizedVersion(object):
    """
    A class to provide a clean interface for setting/retrieving distinct
    version parts divided into major, minor, and patch (following convnetions
    from semver (see http://semver.org/)

    Since a lot of times version parts need to be compared, it provides for
    `int` representations of their string counterparts, with some sanitization
    processing.

    Defaults to '0' or 0 (int) values when values are not set or parsing fails.
    """

    def __init__(self, raw_version):
        self.raw_version = raw_version.strip()
        self.major = '0'
        self.minor = '0'
        self.patch = '0'
        self.garbage = ''
        self.int_major = 0
        self.int_minor = 0
        self.int_patch = 0
        self._version_map = {}
        self._set_versions()

    def _set_int_versions(self):
        version_map = dict(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            garbage=self.garbage)

        # safe int versions that remove non-numerical chars
        # for example 'rc1' in a version like '1-rc1
        for name, value in version_map.items():
            if '-' in value:  # get rid of garbage like -dev1 or -rc1
                value = value.split('-')[0]
            value = float(''.join(c for c in value if c.isdigit()) or 0)
            int_name = "int_%s" % name
            setattr(self, int_name, value)

    def _set_versions(self):
        split_version = (self.raw_version.split('.') + ["0"]*4)[:4]
        self.major, self.minor, self.patch, self.garbage = split_version
        self._set_int_versions()
