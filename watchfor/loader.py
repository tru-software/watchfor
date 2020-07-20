import datetime
import socket
import time
import os
import click
import urllib3
import bs4
import gzip
from urllib.parse import urljoin
from PIL import Image

from typing import List, Dict

from io import BytesIO

from ruamel import yaml


class ConfError(ValueError):
	pass


def echo_time():
	click.secho(datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S "), fg="cyan", nl=False)


def named(name):
	def wrap(f):
		f.get_name = lambda: name
		return f
	return wrap


def open_dir(data):

	for entry in os.listdir(data):

		if not entry.endswith(".yml"):
			continue

		try:
			cfg_path = os.path.abspath(os.path.join(data, entry))

			echo_time()
			click.secho('Reading: ', nl=False)
			click.secho(cfg_path, fg="bright_yellow")

			with open(cfg_path) as f:
				open_yaml(f)

		except ConfError as ex:
			echo_time()
			click.secho('Found error(s) in the file: ', fg='red', nl=False)
			click.secho(cfg_path + " ", fg="bright_yellow", nl=False)
			click.secho(str(ex), fg='bright_white', bg="red")


def open_yaml(f):

	data = yaml.safe_load(f)

	try:
		schema = int(data.get('schema', 1))
	except (ValueError, TypeError):
		raise ConfError(f"Invalid schema version number: {data['schema']}")

	if schema == 1:
		ProcessorV1(data).execute()
	else:
		raise ConfError(f"Invalid schema version: {schema}")


class ProcessorV1:

	def __init__(self, cfg):

		timeout = float(cfg.get('timeout', 10))
		self.http_pool = urllib3.PoolManager(10, timeout=urllib3.Timeout(connect=timeout, read=timeout))
		self.cfg = cfg

		self.default_method = 'GET'
		self.default_headers = {}

	def execute(self):

		data = self.cfg

		echo_time()
		click.secho('Site: ', nl=False)

		url = 'https://{}'.format(data['host'])
		click.secho(url, fg='bright_white', bg="blue")

		self.default_method = data.get('method', 'GET')
		if self.default_method not in ('GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'):
			raise ConfError(f"Invalid method: {self.default_method}")

		headers = {}
		if 'headers' in data:

			if not isinstance(data['headers'], dict):
				raise ConfError(f"Invalid headers list: {data['headers']}")

			for k, v in data.get('headers').items():
				headers[k] = v

		self.default_headers = headers

		if 'checks' in data:
			self.process_checks(url, data['checks'])

	def process_checks(self, base_url, checks):

		for cfg in checks:
			try:
				for url_path, method, headers in self.request_factory(cfg['request'], self.default_method, self.default_headers):

					# if not url_path:
					# 	raise ConfError(f"Invalid request URL: {cfg['request']}")

					url = urljoin(base_url, url_path)

					echo_time()
					click.secho("-" * 80, fg="yellow")

					if 'title' in cfg:
						echo_time()
						click.secho(cfg['title'], fg="bright_white", bold=True)

					response = self.call_url(cfg, url, method, headers)
					processor = ResponseProcessor(self, url, response)

					for response_cfg in cfg['response']:

						functor = processor.create(response_cfg)
						if not functor:
							raise ConfError(f"Invalid response processor: {repr(response_cfg)}")

						try:
							functor()
							self.on_success(response, functor)

						except ValueError as ex:

							self.on_failure(headers, response, functor, ex)
							break

					# if 'checks' in cfg:
					# 	self.process_checks(url, processor.content, cfg['checks'], method, headers)

			except ConfError as ex:
				echo_time()
				click.secho('Cannot open config for request: ', fg='red', nl=False)
				click.secho(repr(cfg['request']), fg="bright_yellow")
				echo_time()
				click.secho(str(ex), fg='bright_white', bg="red")

	def request_factory(self, request, method, headers):

		if request is None:
			yield '', method, headers
			return

		if isinstance(request, str):
			yield request, method, headers
			return

		elif isinstance(request, dict):

			if 'headers' in request:
				headers = {**headers, **request['headers']}

			yield request.get('src') or '', request.get('method') or method, headers
			return

		raise ConfError(f"Invalid request: {repr(request)}")

	def call_url(self, cfg, url, request_method, request_headers):

		echo_time()
		click.secho('Requesting: ', fg='bright_magenta', nl=False)
		click.secho(f' {request_method} ', fg="blue", nl=False)
		click.secho(url, fg="bright_yellow")

		begin = time.time()
		try:
			response = self.http_pool.request(request_method, url, headers=request_headers)
		except socket.timeout as ex:
			end = time.time()
			echo_time()
			click.secho(f"No response: {ex}", fg='bright_white', bg="red")
			return

		end = time.time()

		echo_time()
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

		diff = end - begin
		if diff > 2:
			click.secho(f"[{int(diff * 1000)}ms]", fg='bright_white', bg="red")
		elif diff > 0.8:
			click.secho(f"[{int(diff * 1000)}ms]", fg='bright_cyan')
		else:
			click.secho(f"[{int(diff * 1000)}ms]", fg='bright_green')

		return response

	def on_success(self, response, functor):
		echo_time()
		click.secho(" ✓ Success validation: ", fg='green', nl=False)

		click.secho(functor.get_name() if hasattr(functor, 'get_name') else str(functor), fg='bright_green')

	def on_failure(self, request_headers, response, functor, ex):
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
		for k, v in sorted(response.headers.items(), key=lambda i: i[0]):
			echo_time()
			click.secho(f"  {k}", fg='bright_cyan', nl=False)
			click.secho(f"=", fg='bright_white', nl=False)
			click.secho(f"{v}", fg='bright_magenta')


class ReaderBS4:

	queries: List[Dict]

	def __init__(self, response, content: bytes, features="html.parser", queries=[], query=None):

		self.response = response
		self.content = content
		self.html = bs4.BeautifulSoup(self.content, features=features)

		self.queries = list(queries) + [query] if query else queries
		if not self.queries:
			raise ConfError(f"HTML/XML readers require at least one selector")

	def __call__(self):

		for query in self.queries:

			# https://www.crummy.com/software/BeautifulSoup/bs4/doc/#css-selectors
			# https://facelessuser.github.io/soupsieve/selectors/pseudo-classes/
			nodes = self.html.select(query['selector'])
			if len(nodes) == 0:
				if query.get('optional'):
					continue
				raise ConfError(f"HTML node not found: {query['selector']}")

			action = getattr(self, query['action'], None)
			if not action:
				raise ConfError(f"Invalid action: {query['action']}")

			if 'checks' in query:
				for value in action(nodes, query):
					url = urljoin(self.response.url, value)
					self.response.proccess.process_checks(url, query['checks'])

	def ReadProperty(self, nodes, query):
		for node in nodes:
			yield node[query['property']]

	def ReadContent(self, nodes, query):
		for node in nodes:
			yield node.getText()

	def get_name(self):
		return f"ReaderBS4(\"{self.queries[0]['selector']}\")"


class ResponseProcessor:

	def __init__(self, proccess: ProcessorV1, url, response):
		self.url = url
		self.proccess = proccess
		self.headers = response.headers
		self.content = response.data
		self.response = response

	def create(self, cfg):

		if isinstance(cfg, str):
			return getattr(self, cfg)

		if isinstance(cfg, dict):

			if 'validator' in cfg:
				validator = getattr(self, cfg['validator'])
				args = dict(cfg)
				del args['validator']
				return named(cfg['validator'])(lambda: validator(**args))
			elif 'reader' in cfg:
				reader = getattr(self, cfg['reader'])
				args = dict(cfg)
				del args['reader']
				return reader(**args)
			else:
				raise ConfError(f"Expected validator of follower")

		return None

	def ParseHTML(self, *args, **kwargs):
		return ReaderBS4(self, self.content, *args, features="html.parser", **kwargs)

	def ParseXML(self, *args, **kwargs):
		return ReaderBS4(self, self.content, *args, features="lxml", **kwargs)

	@named("ValidResponse")
	def ValidResponse(self, status=(200, 201)):
		if self.response.status not in status:
			raise ValueError(f"Invalid response status: {self.response.status}, expected one of {status}")

	@named("ValidImage")
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

	@named("ValidContent")
	def ValidContent(self, min_length=None, max_length=None):
		if min_length is not None:

			if len(self.content) < min_length:
				raise ValueError(f"Content length \"{len(self.content)}\" is less then expected {min_length}")

		if max_length is not None:

			if len(self.content) > max_length:
				raise ValueError(f"Content length \"{len(self.content)}\" is longer then expected {max_length}")

	@named("ValidText")
	def ValidText(self):
		if not self.headers['content-type'].startswith("text/"):
			raise ValueError(f"Invalid content-type: {self.headers['content-type']}")

	@named("ValidXML")
	def ValidXML(self):
		if not self.headers['content-type'].startswith("text/xml"):
			raise ValueError(f"Invalid content-type: {self.headers['content-type']}")

	@named("UnGzip")
	def UnGzip(self):
		if not self.headers['content-type'].startswith("application/octet-stream"):
			raise ValueError(f"Invalid content-type: {self.headers['content-type']}")

		stream = BytesIO(self.content)
		with gzip.GzipFile(fileobj=stream, mode='rb') as fo:
			self.content = fo.read()

	@named("ValidRobotsTxt")
	def ValidRobotsTxt(self):

		# TODO: parse self.content as robots.txt
		pass

	@named("ValidFavicon")
	def ValidFavicon(self):
		if not self.headers['content-type'].startswith("image/"):
			raise ValueError(f"Invalid content-type: {self.headers['content-type']}")

	@named("HasHeaders")
	def HasHeaders(self, headers):

		for k, v in headers.items():
			if self.headers.get(k) != v:
				raise ValueError(f"Invalid header: {repr(k)} {repr(self.headers.get(k))} expected {repr(v)}")
