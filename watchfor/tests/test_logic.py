import os
import sys
from io import StringIO
import pytest
import mock
from pathlib import Path
from urllib3_mock import Responses

# FIXME
sys.path = [os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../')] + sys.path

import loader  # noqa


responses = Responses('urllib3')


@responses.activate
def test_request():

	data = """schema: 1
host: www.example.pl
method: GET
headers:
  accept-encoding: gzip, deflate, br
  accept-language: pl,en-US;q=0.9,en;q=0.8
  accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
  user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
checks:
  - request: /
    response:
      - ValidResponse
"""  # noqa

	responses.add('GET', '/', body='OK', status=200, content_type='text/html')

	with mock.patch("loader.ProcessorV1.on_failure", return_value=None) as mock_on_failure:
		with mock.patch("loader.ProcessorV1.on_success", return_value=None) as mock_on_success:
			loader.open_yaml(data)

			assert mock_on_failure.call_count == 0
			assert mock_on_success.call_count == 1


@responses.activate
def test_request_failure():

	data = """schema: 1
host: www.example.pl
method: GET
headers:
  accept-encoding: gzip, deflate, br
  accept-language: pl,en-US;q=0.9,en;q=0.8
  accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
  user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
checks:
  - request: /
    response:
      - ValidResponse
"""  # noqa

	responses.add('GET', '/', body='OK', status=500, content_type='text/html')

	with mock.patch("loader.ProcessorV1.on_failure", return_value=None) as mock_on_failure:
		with mock.patch("loader.ProcessorV1.on_success", return_value=None) as mock_on_success:
			loader.open_yaml(data)

			assert mock_on_failure.call_count == 1
			assert mock_on_success.call_count == 0
