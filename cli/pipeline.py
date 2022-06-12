import os
from contextlib import closing
from multiprocessing import Pool

import click
from config import config as cf
from core import parse_wikitable_html, downloader
from core.utils import io_worker as iw
from core import wikitable_to_image


@click.group()
def cli_pipeline():
    pass


def pool_run_dump(args):
    wikipedia_version, language = args
    downloaded_file = downloader.download_wikipedia_html_dump(
        wikipedia_version, language
    )
    if not downloaded_file:
        return None
    dump_file = parse_wikitable_html.dump_wikitables(
        lang=language, input_file=downloaded_file, progress=True
    )
    return dump_file


def run_dump(wikipedia_version, language, n_threads):
    if language != "all":
        languages = [language]
    else:
        languages = cf.LANGS

    args = [[wikipedia_version, l] for l in reversed(languages)]

    with closing(Pool(processes=n_threads)) as p:
        for i, dump_file in enumerate(p.imap_unordered(pool_run_dump, args)):
            if not dump_file:
                continue
            dump_size = iw.get_size_of_file(os.path.getsize(dump_file))
            print(f"{i + 1}. Dump {language} Saved: {dump_size} - {dump_file}: ")


@cli_pipeline.command()
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
    default="all",
    show_default=True,
    help="Parse the Wikipedia dump of language edition",
)
@click.option(
    "-n", "--n_threads", default=1, show_default=True, help="Run n multiprocessors",
)
def dump_json(wikipedia_version, language, n_threads):
    run_dump(wikipedia_version, language, n_threads)


@cli_pipeline.command()
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
    default="all",
    show_default=True,
    help="Parse the Wikipedia dump of language edition",
)
@click.option(
    "-n", "--n_threads", default=1, show_default=True, help="Run n multiprocessors",
)
@click.option(
    "-c",
    "--compress",
    default=False,
    show_default=True,
    help="Compress the output dataset or not",
)
@click.option(
    "-d",
    "--delete_org",
    default=False,
    show_default=True,
    help="Delete the original folder after compressing",
)
def gen_images(wikipedia_version, language, n_threads, compress, delete_org):
    if language != "all":
        languages = [language]
    else:
        languages = cf.LANGS

    iw.print_status(f"No\tLang\tImages\tErrors\tRunTime")
    for i, language in enumerate(reversed(languages)):
        n_errors, n_images, run_time = wikitable_to_image.gen_images(
            wikipedia_version=wikipedia_version,
            lang=language,
            n_threads=n_threads,
            compress=compress,
            delete_org=delete_org,
        )
        iw.print_status(
            f"{i + 1}\t{language}\t{n_images:,}\t{n_errors:,}\t{run_time:.2f}"
        )


if __name__ == "__main__":
    run_dump(cf.DUMPS_VERSION_WP_HTML, "all", 1)
