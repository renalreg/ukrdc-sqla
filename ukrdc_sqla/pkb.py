"""Deprecated: PKBLink has moved to the ukrdc module."""

import warnings

from .ukrdc import PKBLink  # noqa: F401

warnings.warn(
    "PKBLink has moved; import it from ukrdc_sqla.ukrdc instead.",
    DeprecationWarning,
    stacklevel=2,
)
