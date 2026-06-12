import pytest

from mojawave import MojaWave


@pytest.fixture
def client() -> MojaWave:
    return MojaWave(api_key="sk_test_mw_unit", base_url="https://api.mojawave.test/v1")
