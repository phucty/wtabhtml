import click
from cli import downloader, parser, reader, pipeline

cli_wikitables = click.CommandCollection(
    sources=[
        parser.cli_parser,
        reader.cli_reader,
        downloader.cli_downloader,
        pipeline.cli_pipeline,
    ]
)
