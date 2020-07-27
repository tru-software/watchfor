import os

from ruamel import yaml

from .collector import ICollector
from .exceptions import ConfError
from .processor_v1 import ProcessorV1


class Loader:

	def __init__(self, collector: ICollector):
		self.collector = collector

	def open_dir(self, data):

		for entry in os.listdir(data):

			if entry.startswith("_"):
				# Files started with "_" are omited here, like "_mta.yml"
				continue

			if entry.endswith(".yml"):

				cfg_path = os.path.abspath(os.path.join(data, entry))
				try:
					self.open_file(cfg_path)
				except ConfError as ex:
					self.collector.log_config_error(cfg_path, ex)

	def open_file(self, cfg_path):

		if cfg_path.endswith(".yml"):
			with open(cfg_path) as f:
				self.open_yaml(f, src=cfg_path)
		else:
			raise ConfError(f"Invalid file extension {cfg_path}: should one of [.yml]")

	def open_yaml(self, f, src='memory'):

		data = yaml.safe_load(f)
		self.open_cfg(data, src=src)

	def open_cfg(self, data, src='memory'):

		self.collector.log_open_config(src)

		try:
			schema = int(data.get('schema', 1))
		except (ValueError, TypeError):
			raise ConfError(f"Invalid schema version number: {data['schema']}")

		if schema == 1:
			ProcessorV1(self.collector, data).execute()
		elif schema > 1:
			raise ConfError(f"Unsupported schema version: {schema} - probably you need an upgrade")
		else:
			raise ConfError(f"Invalid schema version: {schema}")
