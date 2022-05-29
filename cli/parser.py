import click
from config import config as cf
from core import parse_wikitable_html


@click.group()
def cli_parser():
    pass


@cli_parser.command()
@click.option(
    "-l",
    "--language",
    default="ja",
    show_default=True,
    help="Parse dump in the langauge",
)
@click.option(
    "-f",
    "--downloaded_file",
    default=None,
    show_default=True,
    help="Directory of the downloaded file (Wikipedia HTML dump)",
)
def parse(language, downloaded_file):
    parse_wikitable_html.dump_wikitables(lang=language, input_file=downloaded_file)
