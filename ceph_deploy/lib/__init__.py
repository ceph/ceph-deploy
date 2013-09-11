"""
This module is meant for vendorizing Python libraries. Most libraries will need
to have some ``sys.path`` alterations done unless they are doing relative
imports.

Do **not** add anything to this module that does not represent a vendorized
library.
"""

import remoto
