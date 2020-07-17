import datetime
import time
import os
import click
import httplib2


from . import loader

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

	loader.open_dir(data)


if __name__ == '__main__':
	cli()
