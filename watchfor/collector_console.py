import datetime
import click


from .loader import ICollector

__all__ = ["CollectorConsole"]


class CollectorConsole(ICollector):

	def echo_time(self):
		click.secho(datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S "), fg="cyan", nl=False)

	def log_open_config(self, cfg_path):
		self.echo_time()
		click.secho('Reading: ', nl=False)
		click.secho(cfg_path, fg="bright_yellow")

	def log_config_error(self, cfg_path, ex):
		self.echo_time()
		click.secho('Found error(s) in the file: ', fg='red', nl=False)
		click.secho(cfg_path + " ", fg="bright_yellow", nl=False)
		click.secho(str(ex), fg='bright_white', bg="red")

	def log_start_site(self, url):
		self.echo_time()
		click.secho('Site: ', nl=False)
		click.secho(url, fg='bright_white', bg="blue")

	def log_start_checks(self, url, cfg):
		self.echo_time()
		click.secho("-" * 80, fg="yellow")

		if 'title' in cfg:
			self.echo_time()
			click.secho(cfg['title'], fg="bright_white", bold=True)

	def log_checks_error(self, cfg, ex):
		self.echo_time()
		click.secho('Cannot open config for request: ', fg='red', nl=False)
		click.secho(repr(cfg['request']), fg="bright_yellow")

		self.echo_time()
		click.secho(str(ex), fg='bright_white', bg="red")

	def log_open_url(self, url, request_method, request_headers):
		self.echo_time()
		click.secho('Requesting: ', fg='bright_magenta', nl=False)
		click.secho(f' {request_method} ', fg="blue", nl=False)
		click.secho(url, fg="bright_yellow")

	def log_open_url_timeout(self, url, diff, ex):
		self.echo_time()
		click.secho(f"No response: {ex}", fg='bright_white', bg="red")

	def log_open_url_response(self, url, request_method, request_headers, diff, response):

		self.echo_time()
		click.secho(" → Response: ", fg="bright_magenta", nl=False)
		status = response.status
		if status >= 500:
			click.secho(str(status), fg='bright_white', bg="red", nl=False)
		elif status >= 400:
			click.secho(str(status), fg='black', bg="bright_yellow", nl=False)
		elif status >= 300:
			click.secho(str(status), fg='black', bg="bright_yellow", nl=False)
		elif status >= 200:
			click.secho(str(status), fg='bright_white', bg="blue", nl=False)

		click.echo(" ", nl=False)

		if diff > 2:
			click.secho(f"[{int(diff * 1000)}ms]", fg='bright_white', bg="red")
		elif diff > 0.8:
			click.secho(f"[{int(diff * 1000)}ms]", fg='bright_cyan')
		else:
			click.secho(f"[{int(diff * 1000)}ms]", fg='bright_green')

	def log_check_success(self, response, functor):
		self.echo_time()
		click.secho(" ✓ Success validation: ", fg='green', nl=False)

		click.secho(functor.get_name() if hasattr(functor, 'get_name') else str(functor), fg='bright_green')

	def log_check_failure(self, url, request_method, request_headers, response, functor, ex):
		self.echo_time()
		click.secho(" 🚫 Validation failed: ", fg='bright_red', nl=False)
		click.secho(str(ex), fg='bright_white', bg="red")

		self.echo_time()
		click.secho(" Request headers ", fg='bright_white', bg="green", bold=True)
		for k, v in sorted(request_headers.items(), key=lambda i: i[0]):
			self.echo_time()
			click.secho(f"  {k}", fg='bright_cyan', nl=False)
			click.secho(f"=", fg='bright_white', nl=False)
			click.secho(f"{v}", fg='bright_magenta')

		self.echo_time()
		click.secho(" Response headers ", fg='bright_white', bg="blue", bold=True)
		for k, v in sorted(response.headers.items(), key=lambda i: i[0]):
			self.echo_time()
			click.secho(f"  {k}", fg='bright_cyan', nl=False)
			click.secho(f"=", fg='bright_white', nl=False)
			click.secho(f"{v}", fg='bright_magenta')
