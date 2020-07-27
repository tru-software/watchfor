from abc import ABC


class ICollector(ABC):

	def log_open_config(self, cfg_path):
		pass

	def log_config_error(self, cfg_path, ex):
		pass

	def log_start_site(self, url):
		pass

	def log_start_checks(self, url, cfg):
		pass

	def log_checks_error(self, cfg, ex):
		pass

	def log_open_url(self, url, request_method, request_headers):
		pass

	def log_open_url_timeout(self, url, diff, ex):
		pass

	def log_open_url_response(self, url, request_method, request_headers, diff, response):
		pass

	def log_check_success(self, url, request_method, request_headers, response, functor):
		pass

	def log_check_failure(self, url, request_method, request_headers, response, functor, ex):
		pass
