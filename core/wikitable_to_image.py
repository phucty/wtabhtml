import bz2
import json
import multiprocessing
import os
import random
import re
import time
from io import BytesIO

import cv2
import numpy as np
import ujson
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import config as cf
from core.parse_wikitable_html import get_jsonl_size
from core.utils import io_worker as iw
from core.utils.io_worker import merge_jsonl_files


def html_to_img(driver, html_content, id_count):
    """converts html to image and bounding boxes of each cell"""
    counter = 1  # This counter is to keep track of the exceptions and stop execution after 10 exceptions have occurred
    add_border = 2
    while True:
        try:
            driver.get("data:text/html;charset=utf-8," + html_content)

            el = driver.find_element_by_tag_name("table")
            png = el.screenshot_as_png

            im = Image.open(BytesIO(png))

            table_loc = el.location

            bboxes = []
            for id in range(id_count):
                # print(id)
                e = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.ID, str(id)))
                )
                txt = e.text.strip()
                lentext = len(txt)
                loc = e.location
                size_ = e.size
                xmin = loc["x"] - table_loc["x"] - add_border
                ymin = loc["y"] - table_loc["y"] - add_border
                xmax = int(size_["width"] + xmin) + add_border * 2
                ymax = int(size_["height"] + ymin) + add_border * 2
                bboxes.append([lentext, txt, xmin, ymin, xmax, ymax])

            return im, bboxes
        except Exception as e:
            counter += 1
            return None, None
            # if counter==10:
            #     return im,None

            # continue


def html_string2list(html_string):
    """this function convert string into list of char and html tag"""
    list_ = []
    idx_tag = -1
    for i, char in enumerate(html_string):
        if char == "<":
            idx_tag = i
        elif idx_tag != -1 and char == ">":
            html_tag = html_string[idx_tag : i + 1]

            # ignore comment inside cell content
            if html_tag.startswith("<!--") or html_tag.startswith("<!["):
                idx_tag = -1
                continue

            list_.append(html_tag)
            idx_tag = -1
        elif idx_tag == -1:
            list_.append(char)

    return list_


def create_style(border_cat):
    """This function will dynamically create stylesheet of tables"""

    style = "<head><style>"
    style += "html{background-color: white;}table{"

    # random center align
    if random.randint(0, 1) == 1:
        style += "text-align:center;"

    style += """border-collapse:collapse;}td,th{padding:6px;padding-left: 6px;padding-right: 6px;"""

    if border_cat == 0:
        style += """ border:1px solid black;} """
    elif border_cat == 2:
        style += """border-bottom:1px solid black;}"""
    elif border_cat == 3:
        style += """border-left: 1px solid black;}
                   th{border-bottom: 1px solid black;} table tr td:first-child, 
                   table tr th:first-child {border-left: 0;}"""
    else:
        style += """}"""

    style += "</style></head>"
    return style


def draw_matrices(img, bboxes, output_file_name):
    """ This function draws visualizations of cell bounding boxes on a table image """
    bboxes = bboxes[:, 2:]

    img = img.astype(np.uint8)
    img = np.dstack((img, img, img))

    im = img.copy()
    pad_ = 3
    for box in bboxes:
        cv2.rectangle(
            im,
            (int(box[0]) + pad_, int(box[1]) + pad_),
            (int(box[2]) - pad_, int(box[3]) - pad_),
            (0, 0, 255),
            1,
        )
    img_name = os.path.join("bboxes/", output_file_name)
    cv2.imwrite(img_name, im)


def check_int_span(s):
    # check span col/row is between 2~20
    if not s.isdigit():
        return False
    if int(s) < 2 or int(s) > 20:
        return False
    return True


def convert_html_to_pubtabnet(table):
    soup = BeautifulSoup(table, "html.parser")

    tables = soup.find_all("table", {"class": re.compile("wikitable*")})
    for table in tables:
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
                    (col.name in ["th", None] and col.name not in ["td"])
                    for col in tag2
                ):
                    tag2.extract()
                    thead.append(tag2)
                    has_header = True
                else:
                    end_header = True
        if has_header:
            table.insert(0, thead)
        table.attrs["border"] = 1

        def filter_attr(bs_obj, white_tags):
            bs_obj.attrs = {
                attr: v for attr, v in bs_obj.attrs.items() if attr in white_tags
            }

        filter_attr(table, ["border", "cellpadding", "style"])
        for a in table.findAll(True):
            filter_attr(a, ["colspan", "headers", "rowspan", "cellpadding", "style"])

        for tag in ["a", "span", "link", "img", "div"]:
            for a in table.findAll(tag):
                a.unwrap()

        for tag in ["sup"]:
            for a in table.findAll(tag):
                a.extract()
        return str(table)


def transform_html_id_text(html_input):
    """
    change all <th> tag inside <thead> to <td> tag
    add <span id=''> to content of <td> tag (generate location of cell content)
    """

    # html_input = convert_html_to_pubtabnet(html_input)
    # html_input = html_input.replace("1px solid #a2a9b1", "1")
    html = """<html>"""
    html += create_style(1)
    html += """<body>"""
    html += html_input
    html += """</body></html>"""

    html = html.replace("> </td>", "></td>")
    html = html.replace("> </th>", "></th>")
    html = html.replace("\n", "")
    # html = html.replace('border="1"', '')

    # print(html)

    idx_count = 0

    table_ = BeautifulSoup(html, "lxml")

    struc_tokens = []
    list_cell_contents = []

    # ############ Remove caption ##############
    # will be changed to remain the table title in a table image
    caption_ = table_.find_all("caption")
    if len(caption_) > 0:
        for cap_ in caption_:
            cap_.string = ""

    # #################get thead and tbody#################
    thead = table_.find_all("thead")
    if len(thead) != 1:
        return None, None, None, idx_count

    tbody = table_.find_all("tbody")
    if len(tbody) != 1:
        return None, None, None, idx_count

    thead_tbody = thead + tbody
    for tag_ in thead_tbody:
        if tag_.name == "thead":
            struc_tokens.append("<thead>")
        else:
            struc_tokens.append("<tbody>")

        #  get tr and td
        for tr in tag_.find_all("tr"):
            if len(tr.find_all("td") + tr.find_all("th")) == 0:
                continue
            struc_tokens.append("<tr>")

            for td in tr.find_all("td") + tr.find_all("th"):
                if td.find_all("table"):
                    # if there is a table inside the cell, then ignore this pattern
                    return None, None, None, idx_count
                if len(td.contents) == 0:
                    list_cell_contents.append([])
                    struc_tokens.append("<td>")
                    struc_tokens.append("</td>")
                    continue
                if td.text.strip() == "":
                    list_cell_contents.append([])
                    struc_tokens.append("<td>")
                    struc_tokens.append("</td>")
                    continue

                # print(''.join(str(el) for el in td.contents))
                # print(html_string2list(''.join(str(el) for el in td.contents)))

                # store the content of this cell
                list_cell_contents.append(
                    html_string2list("".join(str(el) for el in td.contents))
                )
                # add <span id=''> to content of <td> tag to generate location of cell content
                td.string = (
                    "<span id="
                    + str(idx_count)
                    + ">"
                    + "".join(str(el) for el in td.contents)
                    + "</span>"
                )
                idx_count = idx_count + 1

                if (not td.has_attr("colspan")) and (not td.has_attr("rowspan")):
                    struc_tokens.append("<td>")
                    struc_tokens.append("</td>")
                else:
                    struc_tokens.append("<td")
                    if td.has_attr("colspan"):
                        if not check_int_span(td["colspan"]):
                            return None, None, None, idx_count

                        struc_tokens.append(' colspan="' + td["colspan"] + '"')
                    if td.has_attr("rowspan"):
                        if not check_int_span(td["rowspan"]):
                            return None, None, None, idx_count

                        struc_tokens.append(' rowspan="' + td["rowspan"] + '"')

                    struc_tokens.append(">")
                    struc_tokens.append("</td>")

            struc_tokens.append("</tr>")

        if tag_.name == "thead":
            struc_tokens.append("</thead>")
        else:
            struc_tokens.append("</tbody>")

    return struc_tokens, table_.prettify(formatter=None), list_cell_contents, idx_count


def get_chunks(start_id, end_id, n_chunks=1):
    if end_id < 0:
        raise ValueError()

    counts = end_id - start_id + 1
    nums_per_chunk = counts // n_chunks
    chunks = []
    for n in range(n_chunks):
        if n == n_chunks - 1:
            chunks.append([n * nums_per_chunk, end_id])
        else:
            chunks.append([n * nums_per_chunk, (n + 1) * nums_per_chunk])
    return chunks


def parse_wiki_tables_mp(input_file, error_file, save_dir, split_name, chunks):
    """
        multiprocessing to parse raw data.
        One process to do one chunk parsing.
        :param table_chunks:
        :return:
        """
    # self.read_json_tables(table_chunks[1], 1)

    p = multiprocessing.Pool(len(chunks))
    for chunk in chunks:
        args = (input_file, error_file, save_dir, split_name, chunk)
        p.apply_async(read_json_tables, args)
    p.close()
    p.join()


def read_json_tables(input_file, error_file, save_dir, split_name, chunk):
    """
        Read Japanese Wikipedia tables from one table chunk.
        :param: this_chunk
        :param: chunks_idx
        """

    opts = Options()
    opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)

    if input_file.endswith(".bz2"):
        input_file_reader = bz2.BZ2File(input_file)
    else:
        input_file_reader = open(input_file, "r")

    start_id, end_id = chunk

    error_file = f"{error_file}{start_id}_{end_id}.jsonl.bz2"

    if error_file.endswith(".bz2"):
        errors_file_writer = bz2.open(error_file, "wt")
    else:
        errors_file_writer = open(error_file, "w")

    i = 0
    while True:
        line = input_file_reader.readline()
        if not line:
            break
        i += 1
        if i < chunk[0] or i >= chunk[1]:
            continue

        table_obj = ujson.loads(line)
        # iw.print_status(
        #     "[%d, %d] | Table:%d | WD:%s | Index:%d | URL:%s"
        #     % (
        #         chunk[0], chunk[1],
        #         i,
        #         str(table_obj.get("wikidata")),
        #         table_obj["index"],
        #         str(table_obj.get("url")),
        #     ),
        #     is_screen=False,
        # )

        (
            struc_tokens,
            html_with_id,
            list_cell_contents,
            idx_count,
        ) = transform_html_id_text(table_obj["html"])

        if struc_tokens is None:
            # save error patterns to folder
            errors_file_writer.write(ujson.dumps(table_obj))
            errors_file_writer.write("\n")
            continue

        im, bboxes = html_to_img(driver, html_with_id, idx_count)
        if bboxes is None:
            # save error patterns to folder
            errors_file_writer.write(ujson.dumps(table_obj))
            errors_file_writer.write("\n")
            continue
        # Save photo
        dir_sample = f"{save_dir}/{i}"
        im.save(f"{dir_sample}.png", dpi=(600, 600))

        # Save ground truth json
        cells = []
        idx_ = 0
        for cell_token_ in list_cell_contents:
            if len(cell_token_) == 0:
                cell_ = {"tokens": cell_token_}
            else:
                cell_ = {"tokens": cell_token_, "bbox": bboxes[idx_][2:]}
                idx_ += 1

            cells.append(cell_)

        html_json = {"structure": {"tokens": struc_tokens}, "cells": cells}

        # save to folder
        table_sample = {
            "filename": str(i) + ".png",
            "split": split_name,
            "imgid": i,
            "html": html_json,
        }

        with open(f"{dir_sample}.json", "w") as s_json:
            json.dump(table_sample, s_json)

        # # ##########debug
        # with open('bboxes/' + str(i) + '.txt', 'w') as f:
        #     f.write(html_with_id)
        #     f.write(str(table_sample))
        #
        # img = np.asarray(im, np.int64)[:, :, 0]
        # draw_matrices(img, np.array(bboxes), str(i) + '.jpg')
        # # #########################

    driver.quit()


def gen_images(
    wikipedia_version=cf.DUMPS_VERSION_WP_HTML,
    lang="ja",
    start_id=None,
    end_id=None,
    n_threads=8,
    split_name="train",
    compress=False,
    delete_org=False,
):
    start = time.time()
    input_file = f"{cf.DIR_MODELS}/wikitables_html_pubtabnet/{lang}.jsonl.bz2"
    if not os.path.exists(input_file):
        iw.print_status(f"Missing jsonl file: {input_file}")
        from cli.pipeline import run_dump

        run_dump(
            wikipedia_version=wikipedia_version, language=lang, n_threads=n_threads,
        )
        if not os.path.exists(input_file):

            return 0, 0, 0
    save_root = f"{cf.DIR_MODELS}/wikitables_images/"
    save_lang = f"{save_root}{lang}/"
    save_split_name = f"{save_lang}{split_name}/"
    save_errors = f"{save_lang}errors/"
    iw.create_dir(save_root)
    iw.create_dir(save_lang)
    iw.create_dir(save_split_name)
    iw.create_dir(save_errors)

    if start_id is None and end_id is None:
        end_id = get_jsonl_size(input_file)
        start_id = 0

    chunks = get_chunks(start_id=start_id, end_id=end_id, n_chunks=n_threads)

    parse_wiki_tables_mp(
        input_file=input_file,
        error_file=save_errors,
        save_dir=save_split_name,
        split_name=split_name,
        chunks=chunks,
    )

    n_errors = merge_jsonl_files(save_errors[:-1])
    n_images = len(os.listdir(save_split_name)) // 2

    if compress:
        output_file_compressed = f"{save_root}{lang}.tar.bz2"
        iw.compress_folder(
            input_folder=save_lang,
            output_file=output_file_compressed,
            delete_org=delete_org,
        )
        iw.print_status(f"Output file: {output_file_compressed}")
    else:
        iw.print_status(f"Output dataset folder: {save_lang}")
    return n_errors, n_images, time.time() - start
