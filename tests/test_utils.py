import pytest

from fastapi_pagination import utils

utils._EXTENSIONS = [
    "unknown_extension",
    "sqlalchemy",
]


def test_check_installed_extensions():
    utils._CHECK_INSTALLED_EXTENSIONS = True

    with pytest.warns(utils.FastAPIPaginationWarning):
        utils.check_installed_extensions()


def test_check_installed_extensions_disabled(recwarn):
    utils.disable_installed_extensions_check()
    utils.check_installed_extensions()

    assert not recwarn


def test_get_caller():
    assert utils.get_caller(depth=1_000) is None


def _sync_resolve_additional_data(items):
    return {"count": len(items)}


def test_sync_resolve_additional_data():
    assert utils.sync_resolve_additional_data([1, 2, 3], None) == {}
    assert utils.sync_resolve_additional_data([1, 2, 3], {}) == {}
    assert utils.sync_resolve_additional_data([1, 2, 3], _sync_resolve_additional_data) == {"count": 3}


async def _async_resolve_additional_data(items):
    return {"count": len(items)}


@pytest.mark.asyncio
async def test_async_resolve_additional_data():
    assert await utils.async_resolve_additional_data([1, 2, 3], None) == {}
    assert await utils.async_resolve_additional_data([1, 2, 3], {}) == {}
    assert await utils.async_resolve_additional_data([1, 2, 3], _sync_resolve_additional_data) == {"count": 3}
    assert await utils.async_resolve_additional_data([1, 2, 3], _async_resolve_additional_data) == {"count": 3}
