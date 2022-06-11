import click

from core import parse_wikitable_html


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
    parse_wikitable_html.read_wikitable_dumps(input_file, limit)


@cli_reader.command()
@click.option(
    "--input_file", "-i", help="Read the JSON dump of Wikipedia tables",
)
def size(input_file):
    print(parse_wikitable_html.get_jsonl_size(input_file))


@cli_reader.command()
@click.option(
    "--input_folder", "-i", help="The folder of Wikitable JSON dumps",
)
def stats(input_folder):
    parse_wikitable_html.read_wikitable_dumps(input_folder)
