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
@click.option(
    "-t", "--limit_table", default=0, show_default=True, help="Save # number of tables",
)
def parse(language, downloaded_file, limit_table):
    parse_wikitable_html.dump_wikitables(
        lang=language, input_file=downloaded_file, limit=limit_table
    )
