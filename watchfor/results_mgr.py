import datetime
import os
import pickle
import hashlib
import logging

from .collector import ICollector


log = logging.getLogger(__name__)


# TODO: merge this class with locked_open()

class ResultsMgr:
	"""
		ResultsMgr keeps latest checks results to reduce number of duplicated notifications.
	"""

	def __init__(self):
		super().__init__()

		self._latest_results = {}
		self._now = datetime.datetime.now()

	def read_latest_results(self, path):

		if not os.path.exists(path):
			with open(path, "wb") as f:
				pickle.dump({}, f)

		try:
			with open(path, "rb") as f:
				self._latest_results = pickle.load(f)

		except EOFError:
			log.exception(f"Cannot open pickled file {path}")

			with open(path, "wb") as f:
				pickle.dump({}, f)

	def write_latest_results(self, path):
		with open(path, "wb") as f:
			pickle.dump(self._latest_results, f)

	@staticmethod
	def _get_check_key(check):
		calling_request = '{} {}\n{}'.format(check['method'], check['url'], '\n'.join(f'{k}={v}' for k, v in sorted(check['headers'].items())))
		return hashlib.sha1(calling_request.encode()).hexdigest()

	def update_success(self, cfg_path, check):

		key = self._get_check_key(check)

		if cfg_path not in self._latest_results or key not in self._latest_results[cfg_path]:
			return {
				'first_fail': None,
				'raises': 0,
				'fails': 0,
				'latest_alarm': None,
				'alarms_issued': 0
			}

		entry = self._latest_results[cfg_path][key]
		entry['raises'] += 1
		entry['fails'] = 0

		return entry

	def update_failure(self, cfg_path, check):

		key = self._get_check_key(check)

		if cfg_path not in self._latest_results:
			self._latest_results[cfg_path] = {}

		if key not in self._latest_results[cfg_path]:
			self._latest_results[cfg_path][key] = {
				'first_fail': self._now,
				'raises': 0,
				'fails': 0,
				'latest_alarm': None,
				'alarms_issued': 0
			}

		entry = self._latest_results[cfg_path][key]

		entry['fails'] += 1
		entry['raises'] += 0

		return entry

	def alarm_issued(self, cfg_path, check):

		key = self._get_check_key(check)
		entry = self._latest_results[cfg_path][key]
		entry['latest_alarm'] = self._now
		entry['alarms_issued'] += 1

	def recovery_issued(self, cfg_path, check):

		key = self._get_check_key(check)
		if key in self._latest_results[cfg_path]:
			del self._latest_results[cfg_path][key]

		if len(self._latest_results[cfg_path]) == 0:
			del self._latest_results[cfg_path]
