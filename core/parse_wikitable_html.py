import bz2
import json
import os.path
import re
from collections import defaultdict

import bs4
import ujson
from tqdm import tqdm

from core.utils import io_worker as iw
from config import config as cf


def normalize_wikitables_css(soup, table):
    has_header = False
    end_header = False
    thead = soup.new_tag("thead")
    for i1, tag_1 in enumerate(table):
        if tag_1.name != "tbody":
            continue
        # tbody ta
        for i2, tag2 in enumerate(tag_1):
            if tag2.name != "tr":
                continue
            if not end_header and all(
                (col.name in ["th", None] and col.name not in ["td"]) for col in tag2
            ):
                tag2.extract()
                thead.append(tag2)
                has_header = True
            else:
                end_header = True
    if has_header:
        table.insert(0, thead)

    def filter_attr(bs_obj, white_tags):
        bs_obj.attrs = {
            attr: v for attr, v in bs_obj.attrs.items() if attr in white_tags
        }

    filter_attr(table, ["border", "cellpadding", "style"])
    for a in table.findAll(True):
        filter_attr(a, ["colspan", "headers", "rowspan", "cellpadding", "style"])

    for tag in ["a", "span", "link", "img"]:
        for a in table.findAll(tag):
            a.unwrap()

    for tag in ["sup"]:
        for a in table.findAll(tag):
            a.extract()

    # add css
    # table.attrs["background-color"] = "#f8f9fa"
    # table.attrs["color"] = "#202122"
    # table.attrs["margin"] = "1em 0"
    table.attrs["border"] = "1"
    # table.attrs["border-collapse"] = "collapse"
    return table


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

        table = {}
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

        html_table = normalize_wikitables_css(soup, html_table)
        table["html"] = str(html_table)
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

        if line.get("main_entity") and line["main_entity"].get("identifier"):
            update_dict("wikidata", line["main_entity"]["identifier"])
            if not table_obj.get("wikidata"):
                continue

        update_dict("title", line.get("name"))
        update_dict("url", line.get("url"))
        update_dict("html", wikitable.get("html"))
        update_dict("caption", wikitable.get("caption"))
        update_dict("aspects", wikitable.get("aspects"))

        # table_obj["html"] = add_css_wikitable(table_obj["html"])

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


def dump_wikitables(
    lang="ja", input_file=None, outfile=None, limit=0, step=1000, progress=True
):
    if input_file is None:
        input_file = f"{cf.DIR_DUMPS}/{lang}wiki-NS0-{cf.DUMPS_VERSION_WP_HTML}-ENTERPRISE-HTML.json.tar.gz"
    if not os.path.exists(input_file):
        return

    if not outfile:
        if limit:
            outfile = (
                f"{cf.DIR_MODELS}/wikitables_html_pubtabnet/{lang}_{limit}.jsonl.bz2"
            )
        else:
            outfile = f"{cf.DIR_MODELS}/wikitables_html_pubtabnet/{lang}.jsonl.bz2"
    if os.path.exists(outfile):
        return outfile

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

    p_bar = None
    if progress:
        p_bar = tqdm(desc=update_desc(0))

    for parsed_objs in parser:
        if limit and n >= limit:
            break
        if progress and i and i % step == 0:
            p_bar.update(step)
            p_bar.set_description(desc=update_desc(i))
        for parsed_obj in parsed_objs:
            n += 1
            jsonString = ujson.dumps(parsed_obj)
            jsonFile.write(jsonString)
            jsonFile.write("\n")
        i += 1
    if progress:
        p_bar.set_description(desc=update_desc(i))
    jsonFile.close()
    return outfile


def func_modify_table_border(table_obj):
    table_obj["html"] = table_obj["html"].replace("1px solid #a2a9b1", "1")
    return table_obj


def modify_json_dump(input_folder, func):
    dump_files = iw.get_files_from_dir(input_folder, is_sort=True, reverse=True)
    for dump_file in dump_files:
        file_name = os.path.basename(dump_file).split(".")[0]
        dir_output = dump_file + ".tmp"

        if dump_file.endswith(".bz2"):
            output_file = bz2.open(dir_output, "wt")
        else:
            output_file = open(dir_output, "w")

        iter_obj = iw.read_json_file(dump_file)
        for table_obj in tqdm(iter_obj, desc=file_name):
            table_obj = func(table_obj)
            output_file.write(ujson.dumps(table_obj))
            output_file.write("\n")

        output_file.close()
        iw.delete_file(dump_file)
        os.rename(dir_output, dump_file)


def read_wikitable_dumps(input_file: str, limit: int = 0):
    for i, table_obj in enumerate(iw.read_json_file(input_file, limit)):
        print(json.dumps(table_obj, indent=2, ensure_ascii=False))


def get_jsonl_size(input_file: str):
    size = 0
    for _ in iw.read_json_file(input_file):
        size += 1
    return size


def analyze_wikitables(input_folder: str = cf.DIR_MODELS, limit=0, step=1000):
    """
    Show stats of tables
    """
    dump_files = iw.get_files_from_dir(input_folder, is_sort=True, reverse=False)
    stats = defaultdict()

    for dump_file in dump_files:
        file_name = os.path.basename(dump_file).split(".")[0]

        n_tables, n_pages, n_caption, n_aspects = 0, 0, 0, 0

        def update_desc():
            if n_tables and n_pages:
                return f"{file_name}. {n_pages:,} pages | {n_tables/n_pages:.2f} tab/page | {n_caption/n_tables*100:.2f}% cap/tab"
            else:
                return ""

        pre_title = None
        p_bar = tqdm(desc=update_desc())
        try:
            iter_obj = iw.read_json_file(dump_file)
            for table_obj in iter_obj:
                n_tables += 1
                p_bar.update()
                if pre_title != table_obj["title"]:
                    n_pages += 1
                    pre_title = table_obj["title"]
                    if n_pages % step == 0:
                        p_bar.set_description(desc=update_desc())

                if table_obj.get("caption"):
                    n_caption += 1

                if table_obj.get("aspects"):
                    n_aspects += 1
                if limit and n_tables >= 1000:
                    break
            p_bar.set_description(desc=update_desc())
            p_bar.close()
        except EOFError:
            stats[file_name] = [0, 0, 0, 0, 0, 0]
            continue

        stats[file_name] = [
            n_pages,
            n_tables,
            n_caption,
            n_aspects,
            n_caption / n_tables * 100 if n_tables else 0,
            n_aspects / n_tables * 100 if n_tables else 0,
        ]

    headers = [
        "No",
        "Dump",
        "Pages",
        "Tables",
        "Captions",
        "Aspects",
        "Captions/Table",
        "Aspects/Table",
    ]

    iw.print_status("\t".join(headers))
    for i, (file_name, stats_obj) in enumerate(stats.items()):
        iw.print_status(
            f"{i+1}\t{file_name}\t"
            + "\t".join(f"{obj_i:,}" for obj_i in stats_obj[:4])
            + "\t"
            + "\t".join(f"{obj_i:.2f}" for obj_i in stats_obj[4:])
        )
