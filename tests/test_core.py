from unittest.mock import Mock

import pytest

from tarsier import Tarsier
from tarsier.ocr import OCRService


@pytest.fixture
def ocr_service():
    return Mock(spec=OCRService)


def test_init_loads_js_utils(ocr_service):
    tarsier = Tarsier(ocr_service)
    assert tarsier._js_utils is not None
