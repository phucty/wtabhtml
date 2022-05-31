import click

from core.parse_wikitable_html import read_wikitable_dumps


@click.group()
def cli_reader():
    pass


@cli_reader.command()
@click.option(
    "--input_file", "-i", help="Read the JSON dump of Wikipedia tables",
)
@click.option(
    "--limit", "-l", default=0, help="Return first limit tables",
)
def read(input_file, limit):
    read_wikitable_dumps(input_file, limit)
