from core.utils import io_worker as iw

DIR_ROOT = "/Users/phucnguyen/git/wtabhtml"
DUMPS_VERSION_WP_HTML = "20220301"

# Configuration
ENCODING = "utf-8"

# Directories
DIR_DUMPS = f"{DIR_ROOT}/data/dump"
DIR_MODELS = f"{DIR_ROOT}/data/models"
DIR_CONFIG = f"{DIR_ROOT}/config"

# 322 languages of Wikipedia
LANGS = iw.read_tsv_file_first_col(f"{DIR_CONFIG}/LANGS_322.tsv", ENCODING)


URL_WP_HTML = "https://dumps.wikimedia.org/other/enterprise_html/runs/{wikipedia_version}/{lang}wiki-NS0-{wikipedia_version}-ENTERPRISE-HTML.json.tar.gz"
