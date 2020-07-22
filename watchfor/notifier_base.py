import datetime
import os
import pickle
import logging

from .collector import ICollector


log = logging.getLogger(__name__)

ONE_DAY = datetime.timedelta(days=1)


class NotifierBase:

	def __init__(self):
		super().__init__()

		self._latest_results = {}

	def read_latest_results(self, path):

		if not os.path.exists(path):
			with open(path, "wb") as f:
				pickle.dump({}, f)

		try:
			with open(path, "rb") as f:
				results = pickle.load(f)

				now = datetime.datetime.now()
				self._latest_results = {filepath: result for filepath, result in results.items() if result['time'] + ONE_DAY > now}
		except EOFError:
			log.exception(f"Cannot open pickled file {path}")

			with open(path, "wb") as f:
				pickle.dump({}, f)

	def write_latest_results(self, path, collector: ICollector):

		for i in collector.data:
			if i['config'] not in self._latest_results:

				self._latest_results[i['config']] = {
					'time': i['time'],
					# 'errors': i['errors'],
					# 'sites': i['sites']
				}

		with open(path, "wb") as f:
			pickle.dump(self._latest_results, f)

	def has_new_errors(self, collector: ICollector):

		for i in collector.data:

			if i['config'] not in self._latest_results:
				return True

			result = self._latest_results[i['config']]
			if result['time'] + ONE_DAY < i['time']:
				return True

		return False
