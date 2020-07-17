import os
import sys
from io import StringIO
import pytest
import mock
from pathlib import Path
from httplib2 import Response

# FIXME
sys.path = [os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../')] + sys.path

import loader  # noqa


def test_no_schema():

	data = """host: www.example.pl"""
	with mock.patch("loader.ProcessorV1.execute", return_value=None) as mock_execute:
		with mock.patch("loader.ProcessorV1.check_url", return_value=None) as mock_check_url:
			loader.open_yaml(StringIO(data))

			assert mock_execute.call_count == 1
			assert mock_check_url.call_count == 0


@pytest.fixture(scope="module", params=[0, 1000, None, False, "", {}])
def invalid_schema(request):
	return StringIO(f"""schema: {request.param}
host: www.example.pl
""")


def test_invalid_schema(invalid_schema):

	with pytest.raises(loader.ConfError):
		with mock.patch("loader.ProcessorV1.check_url", return_value=None):
			loader.open_yaml(invalid_schema)


def test_invalid_method():

	data = """schema: 1
host: www.example.pl
method: BAD
"""
	with pytest.raises(loader.ConfError):
		with mock.patch("loader.ProcessorV1.check_url", return_value=None):
			loader.open_yaml(data)


@pytest.fixture(scope="module", params=[0, 1000, None, False, "", []])
def invalid_headers(request):
	return StringIO(f"""schema: 1
host: www.example.pl
headers: {request.param}
""")


def test_invalid_headers(invalid_headers):

	with pytest.raises(loader.ConfError):
		with mock.patch("loader.ProcessorV1.check_url", return_value=None):
			loader.open_yaml(invalid_headers)


def test_valid_headers():

	data = """schema: 1
host: www.example.pl
headers:
  accept-encoding: gzip, deflate, br
  accept-language: pl,en-US;q=0.9,en;q=0.8
  accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
  user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
"""  # noqa

	with mock.patch("loader.ProcessorV1.check_url", return_value=None):
		loader.open_yaml(data)
