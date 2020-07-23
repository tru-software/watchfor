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

from . import loader
from . import collector_console, collector_memory
from . import notifier_email
from .locked_open import locked_open
from .exceptions import ConfError


logging.config.dictConfig({
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		'standard': {
			'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
		},
	},
	'handlers': {
		'console': {
			'formatter': 'standard',
			'level': 'INFO',
			'class': 'logging.StreamHandler',
		}
	},
	'loggers': {
		'': {
			'handlers': ['console'],
			'level': 'INFO',
		}
	}
})

log = logging.getLogger(__name__)


@click.group()
def main():
	pass


def echo_time():
	click.secho(datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S "), fg="cyan", nl=False)


@main.command()
@click.option('-d', '--data', help='path to a directory with yml files', default='.', type=click.Path(exists=True))
@click.option('-o', '--output', help='output html file (write perms required)', default=None, type=click.Path())
@click.option('-e', '--email', help='an email address to test MTA config ("_mta.yml")', default=None, type=click.Path())
def debug(data, output, email):

	# TODO: -d - multiple

	data_dir = Path(data)

	if output or email:
		collector = collector_memory.CollectorMemory()
	else:
		collector = collector_console.CollectorConsole()

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
			content = Template(tpl.read()).render(data=collector.data, hostname=hostname)

		if output:
			with open(output, "w") as output:
				output.write(content)

		if email:
			with open(data_dir / "_mta.yml") as mta:
				notitier = notifier_email.EMailNotifier(
					yaml.safe_load(mta)
				)

				notitier.send(content, receivers=[email])


@main.command()
@click.option('-d', '--data', help='path to a directory with yml files', default='.', type=click.Path(exists=True))
@click.option('-s', '--stats', help='path to a stats python-pickle file (write perms required)', default='_stats.json', type=click.Path())
@click.option('-o', '--output', help='output html file (write perms required)', default=None, type=click.Path())
def check(data, stats, output):

	# TODO: -d - multiple

	data_dir = Path(data)

	collector = collector_memory.CollectorMemory()
	processor = loader.Loader(collector)

	with open(data_dir / "_mta.yml") as mta:
		notitier = notifier_email.EMailNotifier(
			yaml.safe_load(mta)
		)

	notitier.read_latest_results(stats)

	with locked_open(stats):

		log.warning(f"Opening configuration from {data_dir}")

		# if data_dir.is_file():
		# 	processor.open_file(data_dir)
		if data_dir.is_dir():
			processor.open_dir(data_dir)
		else:
			raise click.BadParameter("data path is not a directory")

		hostname = socket.gethostname()

		if collector.has_errors or output:

			with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mail_report.mako")) as tpl:
				content = Template(tpl.read()).render(data=collector.data, hostname=hostname)

			if output:
				with open(output, "w") as output:
					output.write(content)

			if notitier.has_new_errors(collector):
				log.warning("Errors found and reporting them")
				notitier.send(content)
			else:
				log.warning("Errors found but seem to be already reported")

			notitier.write_latest_results(stats, collector)

		if not collector.has_errors:
			log.info("All checks has been completed successfully")
