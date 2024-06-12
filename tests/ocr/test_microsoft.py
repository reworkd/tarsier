import pytest

from tarsier import MicrosoftAzureOCRService


def test_invalid_credentials():
    with pytest.raises(ValueError):
        MicrosoftAzureOCRService(
            {
                "type": "service_account",
            }
        )
