import datetime
import socket
import time
import os
import click
import httplib2
import bs4
import gzip
from PIL import Image

from io import BytesIO

from ruamel import yaml


httplib2.CA_CERTS = '/etc/ssl/certs/ca-certificates.crt'


class ConfError(ValueError):
	pass


@click.group()
def cli():
	pass


def echo_time():
	click.secho(datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S "), fg="cyan", nl=False)


@cli.command()
@click.option('-d', '--data', help='path to a directory with yml files', default='.', type=click.Path(exists=True))
def check(data):

	if not os.path.isdir(data):
		raise click.BadParameter("data path is not a directory")

	for entry in os.listdir(data):

		if not entry.endswith(".yml"):
			continue

		try:
			cfg_path = os.path.abspath(os.path.join(data, entry))

			echo_time()
			click.secho('Reading: ', nl=False)
			click.secho(cfg_path, fg="bright_yellow")

			with open(cfg_path) as f:
				data = yaml.safe_load(f)

				try:
					schema = int(data.get('schema', 1))
				except ValueError:
					raise ConfError(f"Invalid schema version number: {data['schema']}")

				if schema == 1:
					validate_v1(data)
				else:
					raise ConfError(f"Invalid schema version: {schema}")
		except ConfError as ex:
			echo_time()
			click.secho('Found error(s) in the file: ', fg='red', nl=False)
			click.secho(cfg_path + " ", fg="bright_yellow", nl=False)
			click.secho(str(ex), fg='bright_white', bg="red")


def validate_v1(data):

	echo_time()
	click.secho('Site: ', nl=False)

	url = 'https://{}'.format(data['host'])
	click.secho(url, fg='bright_white', bg="blue")

	method = data.get('method')
	if method not in ('GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'):
		raise ConfError(f"Invalid method: {method}")

	headers = {}
	if 'headers' in data:
		for k, v in data.get('headers').items():
			headers[k] = v

	process_checks(url, None, data['checks'], method, headers)


def process_checks(url, content, checks, default_method, default_headers):

	for cfg in checks:
		for url_path, method, headers in request_factory(cfg['request'], content, default_method, default_headers):
			if not url_path:
				raise ConfError(f"Invalid request URL: {cfg['request']}")

			if url_path.startswith(('http:', 'https:')):
				pass
			elif url_path.startswith('//'):
				# TODO: get protocol from url
				url_path = 'https:' + url_path
			elif url_path.startswith('/'):
				# TODO: remove path from url
				url_path = url + url_path
			else:
				url_path = url + '/' + url_path

			echo_time()
			click.secho("-" * 80, fg="yellow")

			if 'title' in cfg:
				echo_time()
				click.secho(cfg['title'], fg="bright_white", bold=True)

			check_url(cfg, url_path, method, headers)


def request_factory(request, prev_content, method, headers):
	if isinstance(request, str):
		yield request, method, headers
		return
	elif isinstance(request, dict):

		if 'headers' in request:
			headers = {**headers, **request['headers']}

		if request['src'] in ('ParseHTML', 'ParseXML'):
			html = bs4.BeautifulSoup(prev_content, features="html.parser" if request['src'] == 'ParseHTML' else 'lxml')

			# https://www.crummy.com/software/BeautifulSoup/bs4/doc/#css-selectors
			# https://facelessuser.github.io/soupsieve/selectors/pseudo-classes/
			nodes = html.select(request['selector'])
			if len(nodes) == 0:
				raise ConfError(f"HTML node not found: {request['selector']}")
			if request['action'] == 'ReadProperty':
				for node in nodes:
					yield node[request['property']], method, headers
			elif request['action'] == 'ReadContent':
				for node in nodes:
					yield node.getText(), method, headers
			else:
				raise ConfError(f"Invalid action: {request['action']}")

			return

	raise ConfError(f"Invalid request: {repr(request)}")


def check_url(cfg, url, request_method, request_headers):

	http = httplib2.Http(timeout=30)

	echo_time()
	click.secho('Requesting: ', fg='bright_magenta', nl=False)
	click.secho(f' {request_method} ', fg="blue", nl=False)
	click.secho(url, fg="bright_yellow")

	begin = time.time()
	try:
		headers, content = http.request(url, method=request_method, headers=request_headers)
	except socket.timeout as ex:
		end = time.time()
		echo_time()
		click.secho(f"No response: {ex}", fg='bright_white', bg="red")
		return

	end = time.time()

	echo_time()
	click.secho(" → Response: ", fg="bright_magenta", nl=False)
	status = headers.status
	if status >= 500:
		click.secho(str(status), fg='bright_white', bg="red", nl=False)
	elif status >= 400:
		click.secho(str(status), fg='black', bg="bright_yellow", nl=False)
	elif status >= 300:
		click.secho(str(status), fg='black', bg="bright_yellow", nl=False)
	elif status >= 200:
		click.secho(str(status), fg='bright_white', bg="blue", nl=False)

	click.echo(" ", nl=False)

	diff = end - begin
	if diff > 2:
		click.secho(f"[{int(diff * 1000)}ms]", fg='bright_white', bg="red")
	elif diff > 0.8:
		click.secho(f"[{int(diff * 1000)}ms]", fg='bright_cyan')
	else:
		click.secho(f"[{int(diff * 1000)}ms]", fg='bright_green')

	validator = ResponseValidators(url, headers, content)

	for response_check in cfg['response']:

		functor = validator.create(response_check)
		if not functor:
			raise ConfError(f"Invalid response validator: {repr(response_check)}")

		try:
			functor()
			echo_time()
			click.secho(" ✓ Success validation: ", fg='green', nl=False)

			# In case of HasHeaders the name is "lambda"
			click.secho(functor.__name__, fg='bright_green')
		except ValueError as ex:
			echo_time()
			click.secho(" 🚫 Validation failed: ", fg='bright_red', nl=False)
			click.secho(str(ex), fg='bright_white', bg="red")

			echo_time()
			click.secho(" Request headers ", fg='bright_white', bg="green", bold=True)
			for k, v in sorted(request_headers.items(), key=lambda i: i[0]):
				echo_time()
				click.secho(f"  {k}", fg='bright_cyan', nl=False)
				click.secho(f"=", fg='bright_white', nl=False)
				click.secho(f"{v}", fg='bright_magenta')

			echo_time()
			click.secho(" Response headers ", fg='bright_white', bg="blue", bold=True)
			for k, v in sorted(headers.items(), key=lambda i: i[0]):
				echo_time()
				click.secho(f"  {k}", fg='bright_cyan', nl=False)
				click.secho(f"=", fg='bright_white', nl=False)
				click.secho(f"{v}", fg='bright_magenta')

			break

	if 'checks' in cfg:
		process_checks(url, validator.content, cfg['checks'], request_method, request_headers)


class ResponseValidators:

	def __init__(self, url, headers, content):
		self.url = url
		self.headers = headers
		self.content = content

	def create(self, cfg):
		if isinstance(cfg, str):
			return getattr(self, cfg)

		if isinstance(cfg, dict):

			validator = getattr(self, cfg['validator'])
			args = dict(cfg)
			del args['validator']
			return lambda: validator(**args)

		return None

	def ValidResponse(self):
		if self.headers.status < 200 or self.headers.status > 210:
			raise ValueError(f"Invalid response status: {self.headers.status}")

	def ValidImage(self, min_size=None, format=None):
		if not self.headers['content-type'].startswith("image/"):
			raise ValueError(f"Invalid content-type: {self.headers['content-type']}")

		stream = BytesIO(self.content)
		with Image.open(stream) as img:

			# TODO: cache errors from img.load()
			img.load()

			if min_size is not None:
				w, h = list(map(int, min_size.split('x')))

				if img.width < w:
					raise ValueError(f"Image \"{self.url}\" width {img.width}px is less then expected {w}px")

				if img.height < h:
					raise ValueError(f"Image \"{self.url}\" height {img.height}px is less then expected {h}px")

			if format is not None:
				if img.format != format:
					raise ValueError(f"Image \"{img.format}\" different then expected {format}")

	def ValidContent(self, min_length=None):
		if min_length is not None:

			if len(self.content) < min_length:
				raise ValueError(f"Content length \"{len(self.content)}\" is less then expected {min_length}")

	def ValidText(self):
		if not self.headers['content-type'].startswith("text/"):
			raise ValueError(f"Invalid content-type: {self.headers['content-type']}")

	def ValidXML(self):
		if not self.headers['content-type'].startswith("text/xml"):
			raise ValueError(f"Invalid content-type: {self.headers['content-type']}")

	def UnGzip(self):
		if not self.headers['content-type'].startswith("application/octet-stream"):
			raise ValueError(f"Invalid content-type: {self.headers['content-type']}")

		stream = BytesIO(self.content)
		with gzip.GzipFile(fileobj=stream, mode='rb') as fo:
			self.content = fo.read()

	def ValidRobotsTxt(self):

		# TODO: parse self.content as robots.txt
		pass

	def ValidFavicon(self):
		if not self.headers['content-type'].startswith("image/"):
			raise ValueError(f"Invalid content-type: {self.headers['content-type']}")

	def HasHeaders(self, headers):

		for k, v in headers.items():
			if self.headers.get(k) != v:
				raise ValueError(f"Invalid header: {repr(k)} {repr(self.headers.get(k))} expected {repr(v)}")


if __name__ == '__main__':
	cli()
