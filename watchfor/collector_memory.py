import datetime
import click


from .loader import ICollector

__all__ = ["CollectorMemory"]


class CollectorMemory(ICollector):

	def __init__(self):
		self.data = []
		self.has_errors = False

	def log_open_config(self, cfg_path):
		self.data.append({
			'time': datetime.datetime.now(),
			'config': cfg_path,
			'errors': [],
			'sites': []
		})

	def log_config_error(self, cfg_path, ex):
		self.has_errors = True

		self.data[-1]['errors'].append({
			'time': datetime.datetime.now(),
			'error': ex
		})

	def log_start_site(self, url):
		self.data[-1]['sites'].append({
			'time': datetime.datetime.now(),
			'url': url,
			'errors': [],
			'checks': []
		})

	def log_start_checks(self, url, cfg):
		self.data[-1]['sites'][-1]['checks'].append({
			'type': 'start_check',
			'time': datetime.datetime.now(),
			'cfg': cfg
		})

	def log_checks_error(self, cfg, ex):
		self.has_errors = True

		self.data[-1]['sites'][-1]['errors'].append({
			'type': 'check_error',
			'time': datetime.datetime.now(),
			'error': ex
		})

	def log_open_url(self, url, request_method, request_headers):
		self.data[-1]['sites'][-1]['checks'].append({
			'type': 'open_url',
			'time': datetime.datetime.now(),
			'url': url,
			'method': request_method,
			'headers': request_headers,
		})

	def log_open_url_timeout(self, url, diff, ex):
		self.has_errors = True

		self.data[-1]['sites'][-1]['errors'].append({
			'type': 'open_url_timeout',
			'time': datetime.datetime.now(),
			'url': url,
			'error': ex
		})

	def log_open_url_response(self, url, request_method, request_headers, diff, response):

		self.data[-1]['sites'][-1]['checks'].append({
			'type': 'open_url_response',
			'time': datetime.datetime.now(),
			'url': url,
			'response': response,
			'diff': diff,
			'method': request_method,
			'headers': request_headers
		})

	def log_check_success(self, url, request_method, request_headers, response, functor):

		self.data[-1]['sites'][-1]['checks'].append({
			'time': datetime.datetime.now(),
			'type': 'check_success',

			'url': url,
			'method': request_method,
			'headers': request_headers,

			'danger': 1,  # TODO: implement
			'response': response,
			'check': functor.get_name() if hasattr(functor, 'get_name') else str(functor),
		})

	def log_check_failure(self, url, request_method, request_headers, response, functor, ex):
		self.has_errors = True

		self.data[-1]['sites'][-1]['checks'].append({
			'time': datetime.datetime.now(),
			'type': 'check_failure',

			'url': url,
			'method': request_method,
			'headers': request_headers,

			'danger': 1,  # TODO: implement
			'response': response,
			'error': ex,
			'check': functor.get_name() if hasattr(functor, 'get_name') else str(functor),
		})


class MergeCollectors(ICollector):

	def __init__(self, *args):
		self._collectors = args

	def __getattribute__(self, name):
		if name not in ICollector.__dict__:
			return object.__getattribute__(self, name)

		def tmp(*args, **kwargs):
			latest = None
			for i in self._collectors:
				latest = getattr(i, name)(*args, **kwargs)
			return latest

		return tmp
