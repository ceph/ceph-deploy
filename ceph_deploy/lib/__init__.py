"""
This module is meant for vendorizing Python libraries. Most libraries will need
to have some ``sys.path`` alterations done unless they are doing relative
imports.

Do **not** add anything to this module that does not represent a vendorized
library.

Vendored libraries should go into the ``vendor`` directory and imported from
there. This is so we allow libraries that are installed normally to be imported
if the vendored module is not available.

The import dance here is done so that all other imports throught ceph-deploy
are kept the same regardless of where the module comes from.

The expected way to import remoto would look like this::

    from ceph_deploy.lib import remoto

"""

try:
    # vendored
    from vendor import remoto
except ImportError:
    # normally installed
    import remoto  # noqa
