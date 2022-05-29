import bz2
import csv
import gzip
import logging
import math
import os
import pickle
import shutil
import zlib

import numpy
import ujson


def read_tsv_file_first_col(file_name, encoding):
    with open(file_name, encoding=encoding) as f:
        first_col = [l[0].rstrip() for l in csv.reader(f, delimiter="\t")]
    return first_col


def read_line_from_file(file_name, mode="r"):
    if ".bz2" in file_name:
        reader = bz2.BZ2File(file_name, mode=mode)
    elif ".gz" in file_name:
        reader = gzip.open(file_name, mode=mode)
    else:
        reader = open(file_name, mode=mode)
    if reader:
        for line in reader:
            yield line


def get_size_obj(num, suffix="B"):
    if num == 0:
        return "0"
    magnitude = int(math.floor(math.log(num, 1024)))
    val = num / math.pow(1024, magnitude)
    if magnitude > 7:
        return "{:3.1f}{}{}".format(val, "Yi", suffix)
    return "{:3.1f}{}{}".format(
        val, ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"][magnitude], suffix
    )


def print_status(message, is_screen=True, is_log=True) -> object:
    if isinstance(message, int):
        message = f"{message:,}"

    if is_screen:
        print(message)
    if is_log:
        logging.info(message)


def print_stats_dicts(
    message, print_obj, is_screen=True, is_log=True, delimiter="\t", header=None
):
    print_status(message)
    if header:
        print_status("\t".join(header))
    for i, (k, v) in enumerate(print_obj.items()):
        if isinstance(v, list) or isinstance(v, tuple):
            v = f"{delimiter}".join([str(v_i) for v_i in v])
        print_status(f"{i + 1}{delimiter}{k}{delimiter}{v}", is_screen, is_log)


def delete_folder(folder_dir):
    if os.path.exists(folder_dir):
        shutil.rmtree(folder_dir, ignore_errors=False)
    return True


def delete_file(file_dir):
    if os.path.exists(file_dir):
        os.remove(file_dir)
    return True


def create_dir(file_dir):
    folder_dir = os.path.dirname(file_dir)
    if not os.path.exists(folder_dir):
        os.makedirs(folder_dir)


def save_obj_pkl(file_name, save_object, is_compress=False, is_message=True):
    create_dir(file_name)
    save_file = file_name
    if ".pkl" not in file_name:
        save_file = file_name + ".pkl"
    if is_compress and ".zlib" not in file_name:
        save_file += ".zlib"

    temp_file = save_file + ".temp"

    # Write temp
    with open(temp_file, "wb") as fp:
        if is_compress:
            save_data = zlib.compress(
                pickle.dumps(save_object, pickle.HIGHEST_PROTOCOL)
            )
            fp.write(save_data)
        else:
            pickle.dump(save_object, fp, pickle.HIGHEST_PROTOCOL)

    try:
        if os.path.exists(save_file):
            os.remove(save_file)
    except Exception as message:
        print_status(message)

    os.rename(temp_file, save_file)
    if is_message:
        print_status("Saved: - %d - %s" % (len(save_object), save_file), is_log=False)
    return save_file


def load_obj_pkl(file_name, is_message=False):
    load_obj = None
    if not os.path.exists(file_name) and ".pkl" not in file_name:
        file_name = file_name + ".pkl"

    if not os.path.exists(file_name) and ".zlib" not in file_name:
        file_name = file_name + ".zlib"
    with open(file_name, "rb") as fp:
        if ".zlib" in file_name:
            load_obj = pickle.loads(zlib.decompress(fp.read()))
        else:
            load_obj = pickle.load(fp)
    if is_message and load_obj:
        print_status("%d loaded items - %s" % (len(load_obj), file_name))
    return load_obj


def get_size_of_file(num, suffix="B"):
    """Get human friendly file size
    https://gist.github.com/cbwar/d2dfbc19b140bd599daccbe0fe925597#gistcomment-2845059

    Args:
        num (int): Bytes value
        suffix (str, optional): Unit. Defaults to 'B'.

    Returns:
        str: file size0
    """
    if num == 0:
        return "0"
    magnitude = int(math.floor(math.log(num, 1024)))
    val = num / math.pow(1024, magnitude)
    if magnitude > 7:
        return "{:3.1f}{}{}".format(val, "Yi", suffix)
    return "{:3.1f}{}{}".format(
        val, ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"][magnitude], suffix
    )


def load_object_csv(file_name, encoding="utf-8", retries=2):
    content = []
    if os.path.exists(file_name):
        with open(file_name, "r", encoding=encoding) as f:
            reader = csv.reader(f, delimiter=",")
            for r in reader:
                content.append(r)
    return content


def save_object_csv(file_name, rows):
    create_dir(file_name)
    temp_file = "%s.temp" % file_name
    with open(temp_file, "w") as f:
        try:
            writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
            for r in rows:
                if (
                    isinstance(r, list)
                    or isinstance(r, tuple)
                    or isinstance(r, numpy.ndarray)
                ):
                    writer.writerow(r)
                else:
                    writer.writerow([r])
        except Exception as message:
            print(message)
    if os.path.exists(file_name):
        os.remove(file_name)
    os.rename(temp_file, file_name)


def read_json_file(input_file: str, limit: int = 0):
    if input_file.endswith(".bz2"):
        jsonFile = bz2.BZ2File(input_file)
    else:
        jsonFile = open(input_file, "r")
    i = 0
    limit = int(limit)
    while True:
        line = jsonFile.readline()
        if not line:
            break
        i += 1
        if limit and i > limit:
            break
        table_obj = ujson.loads(line)
        yield table_obj
    jsonFile.close()
