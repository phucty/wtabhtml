import bz2
import os.path
import re

import bs4
import ujson
from tqdm import tqdm

from core.utils import io_worker as iw
from config import config as cf
from contextlib import closing
from multiprocessing import Pool


def extract_html_tables_from_html(html_content):
    results = []
    if not html_content:
        return results

    soup = bs4.BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table", {"class": re.compile("wikitable*")})
    return tables


def add_css_wikitable(html_source):
    """
    Add css of wikitable to the html source
    :param html_source:
    :type html_source:
    :return:
    :rtype:
    """
    if isinstance(html_source, bytes) or isinstance(html_source, str):
        html_source = bs4.BeautifulSoup(html_source, "html.parser")
        tables = html_source.find_all("table", {"class": re.compile("wikitable*")})
    else:
        tables = [html_source]
    for table in tables:
        table.attrs["background-color"] = "#f8f9fa"
        table.attrs["color"] = "#202122"
        table.attrs["margin"] = "1em 0"
        table.attrs["border"] = "1px solid #a2a9b1"
        table.attrs["border-collapse"] = "collapse"

    return str(html_source)


def pool_parse_html_source(line):
    if (
        not line
        or not line.get("article_body")
        or not line["article_body"].get("html")
        or "wikitable" not in line["article_body"]["html"]
    ):
        return None

    if not line.get("main_entity") or not line["main_entity"].get("identifier"):
        return None

    wikitables_html = extract_html_tables_from_html(line["article_body"]["html"])
    if not wikitables_html:
        return None
    table_objs = []
    for i, wikitable in enumerate(wikitables_html):
        table_obj = {
            "title": line.get("name"),
            "url": line.get("url"),
            "index": i,
            "wikidata": line.get("wikidata"),
            "html": add_css_wikitable(wikitable),
        }
        table_objs.append(table_obj)
    return table_objs


def parse_wikitables(input_file=None):
    dump_file = iw.read_line_from_file(input_file, mode="rb")
    for line in dump_file:
        try:
            line_obj = ujson.loads(line)
            parsed_objs = pool_parse_html_source(line_obj)
            if parsed_objs:
                yield parsed_objs
        except ValueError:
            continue


def dump_wikitables(lang="ja", input_file=None, outfile=None, limit=0, step=100):
    if input_file is None:
        input_file = f"{cf.DIR_DUMPS}/{lang}wiki-NS0-{cf.DUMPS_VERSION_WP_HTML}-ENTERPRISE-HTML.json.tar.gz"
    if not os.path.exists(input_file):
        return

    if not outfile:
        if limit:
            outfile = f"{cf.DIR_MODELS}/{lang}_{limit}.jsonl.bz2"
        else:
            outfile = f"{cf.DIR_MODELS}/{lang}.jsonl.bz2"
    iw.create_dir(outfile)
    if outfile.endswith(".bz2"):
        jsonFile = bz2.open(outfile, "wt")
    else:
        jsonFile = open(outfile, "w")

    parser = parse_wikitables(input_file)
    n = 0
    i = 0

    def update_desc(i):
        return f"Parse Wikitable {lang}. Saved {n:,} tables / {i:,} pages"

    p_bar = tqdm(desc=update_desc(0))

    for parsed_objs in parser:
        p_bar.update()
        if limit and n >= limit:
            break
        if i and i % step == 0:
            p_bar.set_description(desc=update_desc(i))
        for parsed_obj in parsed_objs:
            n += 1
            jsonString = ujson.dumps(parsed_obj)
            jsonFile.write(jsonString)
            jsonFile.write("\n")
        i += 1
    p_bar.set_description(desc=update_desc(i))
    jsonFile.close()
    return outfile


def read_wikitable_dumps(input_file: str, limit: int = 0):
    """
    Read Wikipedia tables in Json list format.
    File format: JSON list
    Each line is a json object of
    {
        title: wikipedia title
        wikidata: wikidata ID
        url: the url that link to Wikipedia page
        index: the index of table in the Wikipedia page
        html: html content of table
    }
    """
    for i, table_obj in enumerate(iw.read_json_file(input_file, limit)):
        print(f"{i}. Page " + table_obj["url"] + " - Index: " + str(table_obj["index"]))
        print(table_obj["html"])
