import click
from config import config as cf
from core.downloader import download_wikipedia_html_dump


@click.group()
def cli_downloader():
    pass


@cli_downloader.command()
@click.option(
    "-p",
    "--wikipedia_version",
    default=cf.DUMPS_VERSION_WP_HTML,
    show_default=True,
    help="Version of Wikipedia HTML dump. Find at https://dumps.wikimedia.org/other/enterprise_html/runs/",
)
@click.option(
    "-l",
    "--language",
    default="ja",
    show_default=True,
    help="Download the Wikipedia dump of language edition",
)
def download(wikipedia_version, language):
    download_wikipedia_html_dump(wikipedia_version, language)
