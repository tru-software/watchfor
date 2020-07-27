import datetime
import os
import sys
from io import StringIO, BytesIO
from PIL import Image
import pytest
import mock
from pathlib import Path
from urllib3_mock import Responses

from .. import loader
from ..collector_memory import CollectorMemory
from ..results_mgr import ResultsMgr
from ..alarms import Alarms

from .test_urllib3 import mocked_responses


@pytest.fixture
def config1():
	return {
		'schema': 1,
		'host': 'www.example.pl',
		'method': 'GET',
		'checks': [
			{
				'request': '/',
				'response': ['ValidResponse']
			}
		]
	}


@pytest.fixture
@mocked_responses.activate
def failed_checks(mocker, config1):

	mocked_responses.add('GET', '/', body='ERROR', status=500, content_type='text/html')

	mock_on_failure = mocker.spy(loader.ProcessorV1, "on_failure")
	mock_on_success = mocker.spy(loader.ProcessorV1, "on_success")

	collector = CollectorMemory()
	loader.Loader(collector).open_cfg(config1)

	assert mock_on_failure.call_count == 1
	assert mock_on_success.call_count == 0

	return collector


@pytest.fixture
@mocked_responses.activate
def success_checks(mocker, config1):

	mocked_responses.add('GET', '/', body='OK', status=200, content_type='text/html')

	# No spying here because functions are already mocked by failed_checks() - double mocking doesn't work
	# mock_on_failure = mocker.spy(loader.ProcessorV1, "on_failure")
	# mock_on_success = mocker.spy(loader.ProcessorV1, "on_success")

	collector = CollectorMemory()
	loader.Loader(collector).open_cfg(config1)

	# assert mock_on_failure.call_count == 0
	# assert mock_on_success.call_count == 1

	return collector


def test_failure_reports(failed_checks):

	alarms_cfg = {"default": {
		"when": [{
			"fails": 1,
			"raises": 2,
			"alarms": {
				"mail": ["test@example.pl"]
			}
		}]
	}}

	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)

	results = ResultsMgr()
	alarms(failed_checks, results, "This is an email content")

	assert mta.send.call_count == 1
	assert len(results._latest_results) == 1


def test_failure_2_fails_required(failed_checks):

	alarms_cfg = {"default": {
		"when": [{
			"fails": 2,
			"raises": 1,
			"alarms": {
				"mail": ["test@example.pl"]
			}
		}]
	}}

	results = ResultsMgr()

	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)
	alarms(failed_checks, results, "This is a first email content, which should not be send")

	assert mta.send.call_count == 0
	assert len(results._latest_results) == 1

	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)
	alarms(failed_checks, results, "This is a second email content, which should be send")

	assert mta.send.call_count == 1
	assert len(results._latest_results) == 1


def test_failure_report_only_once(failed_checks):

	alarms_cfg = {"default": {
		"when": [{
			"fails": 1,
			"raises": 1,
			"alarms": {
				"mail": ["test@example.pl"]
			}
		}]
	}}

	results = ResultsMgr()

	now = datetime.datetime.now()

	# First failure: a report should be issued (fails=1)
	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)
	alarms._now = now
	alarms(failed_checks, results, "This is a first email content, which should not be send")

	assert mta.send.call_count == 1
	assert len(results._latest_results) == 1

	# Next check after 10s, with the same results: no report should be issued
	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)
	alarms._now = now + datetime.timedelta(seconds=10)
	alarms(failed_checks, results, "This is a second email content, which should be send")

	assert mta.send.call_count == 0
	assert len(results._latest_results) == 1

	# Next check after 1h, with the same results: no report should be issued
	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)
	alarms._now = now + datetime.timedelta(hours=1)
	alarms(failed_checks, results, "This is a second email content, which should be send")

	assert mta.send.call_count == 0
	assert len(results._latest_results) == 1

	# Next check after 25h, with the same results: a next report should be issued
	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)
	alarms._now = now + datetime.timedelta(hours=25)
	alarms(failed_checks, results, "This is a second email content, which should be send")

	assert mta.send.call_count == 1
	assert len(results._latest_results) == 1

	# One more check after 3 days of failure: after 3 days of failure, a report is sent once per week
	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)
	alarms._now = now + datetime.timedelta(days=4)
	alarms(failed_checks, results, "This is a second email content, which should not be send")

	assert mta.send.call_count == 0
	assert len(results._latest_results) == 1


def test_failure_and_recovery(failed_checks, success_checks):

	alarms_cfg = {"default": {
		"when": [{
			"fails": 1,
			"raises": 1,
			"alarms": {
				"mail": ["test@example.pl"]
			}
		}]
	}}

	results = ResultsMgr()

	now = datetime.datetime.now()

	# Check with success: no report should be issued
	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)
	alarms._now = now
	alarms(success_checks, results, "This is an email content, which should not be send")

	# First failure: a report should be issued (fails=1)
	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)
	alarms._now = now
	alarms(failed_checks, results, "This is a first email content, which should not be send")

	assert mta.send.call_count == 1
	assert len(results._latest_results) == 1

	# Then site is recovered
	mta = mock.Mock()
	alarms = Alarms(alarms_cfg, mta=mta)
	alarms._now = now
	alarms(success_checks, results, "This is an email content, which should not be send")

	assert mta.send.call_count == 0
	assert len(results._latest_results) == 0
