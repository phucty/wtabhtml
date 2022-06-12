# WTabHTML: HTML Wikitables extractor 

### Input:
- Wikipedia HTML dump
- Language

### Output:
File format: JSON list. Each line is a json object of
```
{
    title: wikipedia title
    wikidata: wikidata ID
    url: the url that link to Wikipedia page
    index: the index of table in the Wikipedia page
    html: html content of table
    caption: table caption
    aspects: (Hierachy sections of Wikipedia)  
}
```

### Usage:
#### Download, Extract, and dump wikitables in CR language
```shell
python wtabhtml.py dump -l cr
```

#### Download, Extract, dump wikitables, and generate table images in CR language 

```shell
python wtabhtml.py gen-images -l cr -n 3
```
Note: User can download our [preprocessed dumps](https://drive.google.com/drive/folders/1wU5zdHcb3egxpwyluZCqVBIZnSanUwqN?usp=sharing) then, copy all {LANGUAGE}.jsonl.bz2 (the wikitables dump in PubTabNet format) to `wtabhtml/data/models/wikitables_html_pubtabnet` to generate photo images faster.


If user want to re-run all pipeline, the tool will download Wikipedia HTML dump, extract wikitables, and dump it to `wtabhtml/data/models/wikitables_html_pubtabnet\{LANGUAGE}.jsonl.bz2` file as the following pipeline.

#### Pipeline of Wikitable processing in cr language
```shell
# Download dump
python wtabhtml.py download -l cr
# Parse dump and save json file
python wtabhtml.py parse -l cr
# Read dump
python wtabhtml.py read -l 1 -i ./data/models/cr.jsonl.bz2
# Generate images
python wtabhtml.py gen-images -l cr -n 3
```

### Contact
Phuc Nguyen (`phucnt@nii.ac.jp`)
