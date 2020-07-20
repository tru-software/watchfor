import datetime
import time
import os
import click
import socket

from mako.template import Template

from . import loader
from . import collector_console, collector_memory


class ConfError(ValueError):
	pass


@click.group()
def cli():
	pass


def echo_time():
	click.secho(datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S "), fg="cyan", nl=False)


@cli.command()
@click.option('-d', '--data', help='path to a directory with yml files', default='.', type=click.Path(exists=True))
def debug(data):

	# TODO: -d - multiple

	if not os.path.isdir(data):
		raise click.BadParameter("data path is not a directory")

	loader.Loader(collector_console.CollectorConsole()).open_dir(data)


@cli.command()
@click.option('-d', '--data', help='path to a directory with yml files', default='.', type=click.Path(exists=True))
@click.option('-s', '--stats', help='path to a stats file (write perms required)', default='.', type=click.Path(exists=True))
@click.option('-o', '--output', help='output html file (write perms required)', default='output.html', type=click.Path())
def check(data, stats, output):

	# TODO: -d - multiple

	if not os.path.isdir(data):
		raise click.BadParameter("data path is not a directory")

	collector = collector_memory.CollectorMemory()
	loader.Loader(collector).open_dir(data)

	if collector.has_errors:

		hostname = socket.gethostname()

		with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mail_report.mako")) as tpl:
			content = Template(tpl.read()).render(data=collector.data, hostname=hostname)

			with open(output, "w") as output:
				output.write(content)

		# TODO: collect stats and write to `data`/stats.yml

		# create html from collector.data


		# TODO: read email confs from `data`/mails.yml
		# TODO: send emails
	else:
		print("success")


if __name__ == '__main__':
	cli()
