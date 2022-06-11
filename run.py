from cli import pipeline
from config import config as cf
from core import downloader
from core import parse_wikitable_html
from core.parse_wikitable_html import (
    analyze_wikitables,
    modify_json_dump,
    func_modify_table_border,
)
from core.utils.io_worker import merge_jsonl_files
from core.wikitable_to_image import gen_images


def run_pipeline_dumps_to_jsonl_bz2(wikipedia_version, langs):
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
        # parse_wikitable_html.read_wikitable_dumps(dump_file, limit=0)
    return


if __name__ == "__main__":
    # pipeline.run_dump(cf.DUMPS_VERSION_WP_HTML, "cr", 1)
    # run_pipeline_dumps_to_jsonl_bz2(cf.DUMPS_VERSION_WP_HTML, cf.LANGS)
    # analyze_wikitables(cf.DIR_MODELS + "1")
    gen_images(lang="co", n_threads=5)
    # convert_dumps_to_PubTabnet(cf.DIR_MODELS)
    # modify_json_dump(
    #     "/Users/phucnguyen/git/wtabhtml/data/models/wikitables_html1",
    #     func=func_modify_table_border,
    # )
    # merge_jsonl_files(
    #     "/Users/phucnguyen/git/wtabhtml/data/models/wikitables_images/cr/errors"
    # )
