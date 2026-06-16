"""Unit tests for huntoverlay.constants — static data and URL safety.

Label/translation lookups moved to huntoverlay.i18n; see test_i18n.py.
"""

import pytest

from huntoverlay import constants
from huntoverlay.constants import MAPS


@pytest.mark.unit
def test_maps_are_the_expected_four():
    assert MAPS == ["Stillwater Bayou", "Lawson Delta", "DeSalle", "Mammon's Gulch"]


@pytest.mark.unit
def test_data_urls_are_https():
    # Safety invariant: all remote sources must be https and on the known host.
    for url in (constants.DATA_URL, constants.STYLE_URL):
        assert url.startswith("https://hunt.kamille.ovh/")


@pytest.mark.unit
def test_no_stale_translation_dicts_remain():
    # The *_LABELS_ZH dicts moved to i18n; constants should no longer expose them.
    assert not hasattr(constants, "MAP_LABELS_ZH")
    assert not hasattr(constants, "CATEGORY_LABELS_ZH")
    assert not hasattr(constants, "ACTION_LABELS_ZH")
