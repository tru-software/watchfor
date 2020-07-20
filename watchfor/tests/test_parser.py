import os
import sys
from io import StringIO
import pytest
import mock
from pathlib import Path
from urllib3_mock import Responses

from .. import loader  # noqa


responses = Responses('urllib3')


def test_no_schema(mocker):

	mock_call_url = mocker.spy(loader.ProcessorV1, "call_url")
	mock_execute = mocker.spy(loader.ProcessorV1, "execute")

	data = """host: www.example.pl"""
	loader.open_yaml(StringIO(data))

	assert mock_execute.call_count == 1
	assert mock_call_url.call_count == 0


@pytest.fixture(scope="module", params=[0, 1000, None, False, "", {}])
def invalid_schema(request):
	return StringIO(f"""schema: {request.param}
host: www.example.pl
""")


def test_invalid_schema(invalid_schema, mocker):

	with pytest.raises(loader.ConfError):
		with mock.patch.object(loader.ProcessorV1, "call_url"):
			loader.open_yaml(invalid_schema)


def test_invalid_method(mocker):

	data = """schema: 1
host: www.example.pl
method: BAD
"""
	with pytest.raises(loader.ConfError):
		with mock.patch.object(loader.ProcessorV1, "call_url"):
			loader.open_yaml(data)


@pytest.fixture(scope="module", params=[0, 1000, None, False, "", []])
def invalid_headers(request):
	return StringIO(f"""schema: 1
host: www.example.pl
headers: {request.param}
""")


def test_invalid_headers(invalid_headers, mocker):

	with pytest.raises(loader.ConfError):
		with mock.patch.object(loader.ProcessorV1, "call_url"):
			loader.open_yaml(invalid_headers)


def test_valid_headers(mocker):

	data = """schema: 1
host: www.example.pl
headers:
  accept-encoding: gzip, deflate, br
  accept-language: pl,en-US;q=0.9,en;q=0.8
  accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
  user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
"""  # noqa

	with mock.patch.object(loader.ProcessorV1, "call_url"):
		loader.open_yaml(data)
