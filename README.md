# rssbook

A command-line tool to convert RSS feeds into EPUB books.

## Installation

```bash
pip install .
```

## Usage

Basic usage with default limit (20 items):
```bash
rssbook https://example.com/feed.xml
```

Specify a custom item limit:
```bash
rssbook -l 10 https://example.com/feed.xml
```

## Features

- Converts RSS feed articles into a well-formatted EPUB book
- Includes feed favicon as book cover
- Downloads and embeds article images
- Preserves article formatting and links
- Configurable number of articles to include
- EPUB 2.0 compatible output

## Options

- `url`: The URL of the RSS feed (required)
- `-l, --limit`: Maximum number of items to include (default: 20)

## Output

The tool creates an EPUB file in the current directory, named after the feed title (with spaces replaced by hyphens).
