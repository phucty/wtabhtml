from config import config as cf
from core import downloader
from core import parse_wikitable_html


def run_pipeline(wikipedia_version, langs):
    for lang in langs:
        # 1. Download Wikipedia HTML dump
        downloaded_file = downloader.download_wikipedia_html_dump(
            wikipedia_version, lang
        )
        # 2. Parse HTML dump
        dump_file = parse_wikitable_html.dump_wikitables(
            lang=lang, input_file=downloaded_file
        )
        # 3. Read the first three tables
        parse_wikitable_html.read_wikitable_dumps(dump_file, limit=3)
    return


if __name__ == "__main__":
    run_pipeline(cf.DUMPS_VERSION_WP_HTML, ["cr"])
