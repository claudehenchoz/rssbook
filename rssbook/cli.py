"""Command-line interface for rssbook."""

import argparse
import sys
from .core import create_epub

def main():
    """Entry point for the rssbook command."""
    parser = argparse.ArgumentParser(
        description='Convert RSS feed to EPUB book'
    )
    parser.add_argument(
        'url',
        help='URL of the RSS feed'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=20,
        help='Maximum number of items to include (default: 20)'
    )
    
    args = parser.parse_args()
    
    try:
        output_path = create_epub(args.url, args.limit)
        print(f"Successfully created EPUB: {output_path}")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
