import datetime
import time
import os
import click
import socket
import yaml
import logging
import logging.config
from pathlib import Path

from mako.template import Template

from . import logging_config

from . import loader
from .collector_memory import CollectorMemory, MergeCollectors
from .collector_console import CollectorConsole
from . import notifier_email
from .results_mgr import ResultsMgr
from .locked_open import locked_open
from .exceptions import ConfError
from .alarms import Alarms


log = logging.getLogger(__name__)


@click.group()
def main():
	pass


@main.command()
@click.option('-d', '--data', help='path to a directory with yml files', default='.', type=click.Path(exists=True))
@click.option('-o', '--output', help='output html file (write perms required)', default=None, type=click.Path())
@click.option('-e', '--email', help='an email address to test MTA config ("_mta.yml") - always sends report', default=None, type=click.Path())
def debug(data, output, email):

	# TODO: -d - multiple

	data_dir = Path(data)
	collector = CollectorConsole()
	collector_memory = None

	if output or email:
		collector_memory = CollectorMemory()
		collector = MergeCollectors(
			collector,
			collector_memory
		)

	processor = loader.Loader(collector)

	if data_dir.is_file():
		processor.open_file(data_dir)
	elif data_dir.is_dir():
		processor.open_dir(data_dir)
	else:
		raise click.BadParameter("data path is not a directory or file")

	if output or email:
		hostname = socket.gethostname()

		with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mail_report.mako")) as tpl:
			content = Template(tpl.read()).render(data=collector_memory.data, hostname=hostname)

		if output:
			with open(output, "w") as output:
				output.write(content)

		if email:
			with open(data_dir / "_mta.yml") as mta_cfg:
				mta = notifier_email.EMailNotifier(
					yaml.safe_load(mta_cfg)
				)

			alarms = Alarms({
				'default': {
					'when': [
						{
							'danger': 0,
							'fails': 0,
							'raises': 1,
							'alarms': {
								'mail': [email]
							}
						}
					]
				}
			}, mta=mta)

			results = ResultsMgr()
			alarms(collector_memory, results, content)


@main.command()
@click.option('-d', '--data', help='path to a directory with yml files', default='.', type=click.Path(exists=True))
@click.option('-s', '--stats', help='path to a stats python-pickle file (write perms required)', default='_stats.pickle', type=click.Path())
@click.option('-o', '--output', help='output html file (write perms required)', default=None, type=click.Path())
def check(data, stats, output):

	# TODO: -d - multiple

	data_dir = Path(data)
	hostname = socket.gethostname()

	collector = CollectorMemory()
	processor = loader.Loader(collector)

	with open(data_dir / "_mta.yml") as mta_cfg:
		mta = notifier_email.EMailNotifier(
			yaml.safe_load(mta_cfg)
		)

	with open(data_dir / "_alarms.yml") as alarms_cfg:
		alarms = Alarms(yaml.safe_load(alarms_cfg), mta=mta)

	results = ResultsMgr()
	results.read_latest_results(stats)

	with locked_open(stats):

		log.warning(f"Opening configuration from {data_dir}")

		# if data_dir.is_file():
		# 	processor.open_file(data_dir)
		if data_dir.is_dir():
			processor.open_dir(data_dir)
		else:
			raise click.BadParameter("data path is not a directory")

		if collector.has_errors or output:

			with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mail_report.mako")) as tpl:
				content = Template(tpl.read()).render(data=collector.data, hostname=hostname)

			if output:
				with open(output, "w") as output:
					output.write(content)

			alarms(collector, results, content)

			results.write_latest_results(stats)

		if not collector.has_errors:
			log.info("All checks has been completed successfully")
