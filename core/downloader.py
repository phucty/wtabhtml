from tqdm import tqdm

from config import config as cf
import os
from core.utils import io_worker as iw
import requests


def download_file(download_url):
    dump_file = download_url.split("/")[-1]
    downloaded_file = f"{cf.DIR_DUMPS}/{dump_file}"

    if os.path.exists(downloaded_file):
        return downloaded_file
    iw.create_dir(downloaded_file)
    r = requests.get(download_url, stream=True)
    if r.status_code != 200:
        return None
    p_bar = tqdm(
        total=int(r.headers.get("content-length", 0)),
        unit="B",
        unit_scale=True,
        desc=dump_file,
    )
    with open(f"{cf.DIR_DUMPS}/{dump_file}", "wb") as f:
        for data in r.iter_content(10240):
            p_bar.update(len(data))
            f.write(data)
    p_bar.close()
    return downloaded_file


def download_wikipedia_html_dump(wikipedia_version=cf.DUMPS_VERSION_WP_HTML, lang="ja"):
    # Download Wikipedia dumps
    url = cf.URL_WP_HTML.format(wikipedia_version=wikipedia_version, lang=lang)
    downloaded_file = download_file(url)
    if downloaded_file:
        print(f"Downloaded: {url}")
    else:
        print(f"Error: {url}")
    return downloaded_file
