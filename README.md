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
```shell
# Extract wikitables from dump of cr language
# Download dump
python wtabhtml.py download -l cr
# Parse dump and save json file
python wtabhtml.py parse -l cr
# Read dump
python wtabhtml.py read -l 1 -i ./data/models/cr.jsonl.bz2 
```

```shell
python wtabhtml.py dump -l cr
```

### Example:
```shell
python run.py
```

### Contact
Phuc Nguyen (`phucnt@nii.ac.jp`)
