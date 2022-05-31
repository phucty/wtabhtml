import bz2
import json
import os.path
import re

import bs4
import ujson
from tqdm import tqdm

from core.utils import io_worker as iw
from config import config as cf


def extract_html_tables_from_html(html_content):
    results = []
    if not html_content:
        return results

    soup = bs4.BeautifulSoup(html_content, "html.parser")
    html_tables = soup.find_all("table", {"class": re.compile("wikitable*")})
    tables = []
    for i, html_table in enumerate(html_tables):

        # Check this table is a nested table or not
        # We ignore the nested tables, just process wikitables do not have any wikitable inside
        sub_wikitables = html_table.find("table", {"class": re.compile("wikitable*")})
        if sub_wikitables:
            continue

        table = {"html": html_table}
        # Get table caption
        tag_caption = html_table.find("caption")
        if tag_caption:
            table["caption"] = tag_caption.get_text().strip()

        # Get section hierarchy
        cur = html_table
        while True:
            section = cur.find_parent("section")
            if not section:
                break
            section_name = section.next
            if section_name and section_name.name in cf.HTML_HEADERS:
                if table.get("aspects") is None:
                    table["aspects"] = []
                table["aspects"].append(section_name.get_text())
            cur = section

        if table.get("aspects") and len(table["aspects"]) > 1:
            table["aspects"] = table["aspects"][::-1]
        tables.append(table)

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
        table_obj = {"index": i}

        def update_dict(attr, value):
            if value:
                table_obj[attr] = value

        update_dict("title", line.get("name"))
        update_dict("url", line.get("url"))
        update_dict("wikidata", line.get("wikidata"))
        update_dict("html", wikitable.get("html"))
        update_dict("caption", wikitable.get("caption"))
        update_dict("aspects", wikitable.get("aspects"))

        table_obj["html"] = add_css_wikitable(table_obj["html"])

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
        print(json.dumps(table_obj, indent=2, ensure_ascii=False))
