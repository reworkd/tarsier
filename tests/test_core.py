from unittest.mock import Mock

import pytest

from tarsier import Tarsier
from tarsier.ocr import OCRService


@pytest.fixture
def ocr_service():
    return Mock(spec=OCRService)


def test_init_js_utils_dne(ocr_service):
    Tarsier._JS_TAG_UTILS = "unknown.js"

    with pytest.raises(ValueError):
        Tarsier(ocr_service)


def test_init_loads_js_utils(ocr_service):
    tarsier = Tarsier(ocr_service)
    assert tarsier._js_utils is not None
