"""Unit tests for huntoverlay.images — image cache logic (no network)."""

import os

import pytest

from huntoverlay import images


@pytest.mark.unit
@pytest.mark.parametrize(
    "url,ok",
    [
        ("https://i.imgur.com/abc.png", True),
        ("http://i.imgur.com/abc.jpg", True),
        ("https://imgur.com/abc.png", True),
        ("https://evil.com/abc.png", False),       # host not whitelisted
        ("ftp://i.imgur.com/abc.png", False),       # scheme not http(s)
        ("not a url", False),
        ("", False),
    ],
)
def test_is_allowed_image_url(url, ok):
    assert images.is_allowed_image_url(url) is ok


@pytest.mark.unit
def test_cache_filename_deterministic_and_keeps_ext():
    a = images.cache_filename("https://i.imgur.com/abc.png")
    b = images.cache_filename("https://i.imgur.com/abc.png")
    assert a == b
    assert a.endswith(".png")
    assert images.cache_filename("https://i.imgur.com/x.jpeg").endswith(".jpeg")


@pytest.mark.unit
def test_cache_filename_unknown_ext():
    assert images.cache_filename("https://i.imgur.com/noext").endswith(".img")


@pytest.mark.unit
def test_cache_filename_distinct_for_distinct_urls():
    assert images.cache_filename("https://i.imgur.com/a.png") != \
        images.cache_filename("https://i.imgur.com/b.png")


@pytest.mark.unit
def test_collect_image_urls_dedupes_and_filters():
    data = [
        {"n": "DeSalle", "armories": [
            {"c": [1, 2], "u": ["https://i.imgur.com/a.png"]},
            {"c": [3, 4], "u": ["https://i.imgur.com/a.png", "https://i.imgur.com/b.jpg"]},
            {"c": [5, 6], "u": ["https://evil.com/x.png"]},  # filtered out
            {"c": [7, 8]},                                    # no images
        ]},
    ]
    urls = images.collect_image_urls(data)
    assert urls == ["https://i.imgur.com/a.png", "https://i.imgur.com/b.jpg"]


@pytest.mark.unit
def test_collect_image_urls_defensive():
    assert images.collect_image_urls(None) == []
    assert images.collect_image_urls("notalist") == []
    assert images.collect_image_urls([{"armories": "notalist"}]) == []


@pytest.mark.unit
def test_missing_images(tmp_path):
    cache = str(tmp_path)
    urls = ["https://i.imgur.com/a.png", "https://i.imgur.com/b.png"]
    # Pre-create the cache file for the first URL.
    open(images.cache_path(cache, urls[0]), "w").close()
    miss = images.missing_images(cache, urls)
    assert miss == ["https://i.imgur.com/b.png"]


@pytest.mark.unit
def test_cache_path_under_dir():
    p = images.cache_path("/tmp/cache", "https://i.imgur.com/a.png")
    assert p.startswith("/tmp/cache")
    assert os.path.basename(p).endswith(".png")


@pytest.mark.unit
def test_cleanup_partials(tmp_path):
    cache = str(tmp_path)
    # Two .part leftovers + one real cached file.
    open(os.path.join(cache, "aaa.png.part"), "w").close()
    open(os.path.join(cache, "bbb.jpg.part"), "w").close()
    open(os.path.join(cache, "ccc.png"), "w").close()
    removed = images.cleanup_partials(cache)
    assert removed == 2
    # Real cache file survives; .part files gone.
    assert os.path.isfile(os.path.join(cache, "ccc.png"))
    assert not os.path.isfile(os.path.join(cache, "aaa.png.part"))


@pytest.mark.unit
def test_cleanup_partials_missing_dir():
    assert images.cleanup_partials("/no/such/dir") == 0
