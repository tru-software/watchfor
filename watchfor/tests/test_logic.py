import os
import sys
from io import StringIO, BytesIO
from PIL import Image
import pytest
import mock
from pathlib import Path
from urllib3_mock import Responses

from .. import loader, collector_memory

from .test_urllib3 import mocked_responses


def open_yaml(data):
	return loader.Loader(collector_memory.CollectorMemory()).open_yaml(data)


@mocked_responses.activate
def test_request(mocker):

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

	mocked_responses.add('GET', '/', body='OK', status=200, content_type='text/html')

	mock_on_failure = mocker.spy(loader.ProcessorV1, "on_failure")
	mock_on_success = mocker.spy(loader.ProcessorV1, "on_success")

	open_yaml(data)

	assert mock_on_failure.call_count == 0
	assert mock_on_success.call_count == 1


@mocked_responses.activate
def test_request_failure(mocker):

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

	mocked_responses.add('GET', '/', body='OK', status=500, content_type='text/html')

	mock_on_failure = mocker.spy(loader.ProcessorV1, "on_failure")
	mock_on_success = mocker.spy(loader.ProcessorV1, "on_success")

	open_yaml(data)

	assert mock_on_failure.call_count == 1
	assert mock_on_success.call_count == 0


@mocked_responses.activate
def test_nested_requests(mocker):

	data = """schema: 1
host: www.example.pl
method: GET
protocol: https
timeout: 10.0
headers:
  accept-encoding: gzip, deflate, br
  accept-language: pl,en-US;q=0.9,en;q=0.8
  accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
  user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
checks:
  - request: /
    response:
      - ValidResponse
      - validator: HasHeaders
        headers:
          content-type: text/html; charset=utf-8
      - reader: ParseHTML
        query:
          selector: html head meta[property="og:image"]
          action: ReadProperty
          property: content
          checks:
            - request:
              response:
              - ValidResponse
              - validator: ValidImage
                min_size: 100x100
"""  # noqa

	content = """
<html>
<head>
	<meta property="og:image" content="/path-to-image.jpg" />
</head>
<body>
</body
</html>
"""  # noqa

	buf = BytesIO()
	Image.new('RGB', (120, 120), color='red').save(buf, "JPEG")

	mocked_responses.add('GET', '/', body=content, status=200, content_type='text/html; charset=utf-8')
	mocked_responses.add('GET', '/path-to-image.jpg', body=buf.getvalue(), status=200, content_type='image/jpeg')

	mock_call_url = mocker.spy(loader.ProcessorV1, "call_url")
	mock_on_failure = mocker.spy(loader.ProcessorV1, "on_failure")
	mock_on_success = mocker.spy(loader.ProcessorV1, "on_success")

	open_yaml(data)

	assert mock_call_url.call_count == 2
	assert mock_on_failure.call_count == 0
	assert mock_on_success.call_count == 5
