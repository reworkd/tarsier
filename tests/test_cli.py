import pytest

from tarsier.__main__ import parse_args, main


def test_parse_args_default(mocker):
    test_args = [
        'tarsier',
        'path/to/credentials.json',
        'http://example.com'
    ]
    mocker.patch('sys.argv', test_args)

    args = parse_args()
    assert args.credentials_path == 'path/to/credentials.json'
    assert args.url == 'http://example.com'
    assert args.verbose is False
    assert args.ocr_provider == 'google'


def test_parse_args_non_default(mocker):
    test_args = [
        'tarsier',
        'path/to/credentials.json',
        'http://example.com',
        '--verbose',
        '--ocr_provider', 'microsoft'
    ]
    mocker.patch('sys.argv', test_args)

    args = parse_args()
    assert args.credentials_path == 'path/to/credentials.json'
    assert args.url == 'http://example.com'
    assert args.verbose is True
    assert args.ocr_provider == 'microsoft'


# noinspection PyTypeChecker
@pytest.mark.asyncio
async def test_main_unknown_provider():
    with pytest.raises(ValueError):
        await main(__file__, 'http://example.com', True, 'unknown')

