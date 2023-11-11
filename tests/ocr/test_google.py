import pytest

from tarsier import GoogleVisionOCRService


def test_invalid_credentials():
    with pytest.raises(ValueError):
        GoogleVisionOCRService(
            {
                "type": "service_account",
            }
        )
