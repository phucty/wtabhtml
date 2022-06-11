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
Download, Extract, and dump wikitables in CR language
```shell
python wtabhtml.py dump -l cr
```

Download, Extract, dump wikitables, and generate table images in CR language
```shell
python wtabhtml.py gen-images -l cr -n 3
```

Pipeline of Wikitable processing in cr language
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
