"""
RSS to EPUB Converter
Converts RSS feed articles into an EPUB book with proper formatting and metadata.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

import feedparser
from trafilatura import fetch_url, extract
from lxml import etree
from ebooklib import epub
from slugify import slugify
from io import StringIO, BytesIO
import re
import requests
from urllib.parse import urljoin, urlparse
import mimetypes
import hashlib
import imghdr
import favicon

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FeedMetadata:
    """Data class to store RSS feed metadata."""
    title: str
    link: str
    description: str

@dataclass
class FeedItem:
    """Data class to store individual RSS feed items."""
    title: str
    link: str
    published: str
    content: Optional[str] = None

class HTMLToXHTMLConverter:
    """Handles conversion of HTML content to XHTML format for EPUB 2.0."""
    
    @staticmethod
    def convert(html_string: str) -> str:
        """
        Convert HTML string to EPUB 2.0 compliant XHTML format.
        """
        try:
            parser = etree.HTMLParser(remove_blank_text=True)
            tree = etree.parse(StringIO(html_string), parser)
            
            # Use EPUB 2.0 compatible doctype
            doctype = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" '
                      '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">')
            
            xhtml_string = etree.tostring(
                tree.getroot(),
                encoding='unicode',
                doctype=doctype,
                pretty_print=True,
                method='xml'
            )
            
            # Ensure XHTML 1.1 compliance
            xhtml_string = re.sub(r'<([^>]+)/>', r'<\1 />', xhtml_string)
            
            # Replace HTML5 tags with div elements and class names
            html5_tags = ['article', 'section', 'nav', 'aside', 'header', 'footer']
            for tag in html5_tags:
                xhtml_string = re.sub(
                    f'<{tag}([^>]*)>', 
                    f'<div class="{tag}"\\1>', 
                    xhtml_string
                )
                xhtml_string = re.sub(f'</{tag}>', '</div>', xhtml_string)
            
            return xhtml_string
            
        except etree.ParserError as e:
            raise ValueError(f"Failed to parse HTML: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error converting to XHTML: {str(e)}")

class RSSFeedParser:
    """Handles RSS feed parsing and content extraction."""
    
    def __init__(self, feed_url: str):
        self.feed_url = feed_url
        
    def get_feed_metadata(self) -> FeedMetadata:
        """Extract feed metadata."""
        feed_data = feedparser.parse(self.feed_url)
        return FeedMetadata(
            title=feed_data.feed.title,
            link=feed_data.feed.link,
            description=feed_data.feed.description
        )
    
    def get_feed_items(self, limit: Optional[int] = None) -> List[FeedItem]:
        """
        Extract feed items with optional limit.
        
        Args:
            limit: Maximum number of items to extract
            
        Returns:
            List of FeedItem objects
        """
        feed_data = feedparser.parse(self.feed_url)
        entries = feed_data.entries[:limit] if limit else feed_data.entries
        
        return [
            FeedItem(
                title=item.title,
                link=item.link,
                published=item.published
            )
            for item in entries
        ]

class EPUBCreator:
    """Handles creation of EPUB book from feed content."""
    
    def __init__(self, metadata: FeedMetadata):
        self.metadata = metadata
        self.book = epub.EpubBook()
        self.converter = HTMLToXHTMLConverter()
        self._initialize_book()
        self.downloaded_images = {}
        
    def _create_cover_page(self) -> epub.EpubHtml:
        """Create a cover page with feed icon and metadata."""
        try:
            # Get feed base path
            parsed = urlparse(self.metadata.link)
            feed_domain = parsed.netloc
            
            # Construct favicon URL
            g_favicon_url = f"https://www.google.com/s2/favicons?domain={feed_domain}&sz=256"
            
            # Get largest favicon from the feed's website
            icon_response = requests.get(g_favicon_url, timeout=10)
            icon_response.raise_for_status()
            
            # Save icon to EPUB
            icon_data = icon_response.content
            ext, mime_type = self._get_image_info(icon_data)
            icon_hash = "cover_icon" + hashlib.md5(g_favicon_url.encode()).hexdigest()
            icon_filename = f'images/{icon_hash}{ext}'
            
            icon_item = epub.EpubItem(
                uid=icon_hash,
                file_name=icon_filename,
                media_type=mime_type,
                content=icon_data
            )
            self.book.add_item(icon_item)
            
            # Create cover page content with centered icon and metadata
            cover_content = f"""
            <div style="text-align: center; padding: 20px;">
                <div style="margin: 50px auto;">
                    <img src="{icon_filename}" style="max-width: 200px; display: block; margin: 0 auto;" />
                </div>
                <h1 style="font-size: 24px; margin: 20px 0;">{self.metadata.title}</h1>
                <p style="font-size: 16px; color: #666; margin: 10px 0;">{self.metadata.description}</p>
            </div>
            """
            
            # Create EPUB cover page
            cover = epub.EpubHtml(
                title='Cover',
                file_name='cover.xhtml',
                lang='en'
            )
            cover.content = self.converter.convert(cover_content)
            return cover
            
        except Exception as e:
            logger.error(f"Failed to create cover page: {str(e)}")
            # Return a simple text-only cover if icon fetching fails
            cover = epub.EpubHtml(
                title='Cover',
                file_name='cover.xhtml',
                lang='en'
            )
            cover_content = f"""
            <div style="text-align: center; padding: 20px;">
                <h1 style="font-size: 24px; margin: 20px 0;">{self.metadata.title}</h1>
                <p style="font-size: 16px; color: #666; margin: 10px 0;">{self.metadata.description}</p>
            </div>
            """
            cover.content = self.converter.convert(cover_content)
            return cover

    def _initialize_book(self):
        """Initialize EPUB book with EPUB 2.0 compatible metadata."""
        self.book.set_identifier('rssbook6232146')
        self.book.set_title(self.metadata.description)
        self.book.set_language('en')
        self.book.add_author('rssbook.py')
        
        # Add EPUB 2.0 specific metadata
        self.book.add_metadata('DC', 'creator', 'rssbook.py')
        self.book.add_metadata('DC', 'publisher', 'RSS to EPUB Converter')
        self.book.add_metadata('DC', 'source', self.metadata.link)
        
    def _get_image_info(self, image_data: bytes) -> tuple[str, str]:
        """
        Detect image type and return appropriate extension and mime type.
        """
        # Detect actual image type from data
        img_type = imghdr.what(None, image_data)
        if img_type is None:
            return '.jpg', 'image/jpeg'  # fallback
            
        # Map image types to extensions and MIME types
        type_map = {
            'jpeg': ('.jpg', 'image/jpeg'),
            'jpg': ('.jpg', 'image/jpeg'),
            'png': ('.png', 'image/png'),
            'gif': ('.gif', 'image/gif'),
            'webp': ('.webp', 'image/webp'),
        }
        
        return type_map.get(img_type, ('.jpg', 'image/jpeg'))

    def _download_image(self, img_url: str, base_url: str) -> tuple[str, bytes]:
        """Download image and return filename and content."""
        try:
            # Handle relative URLs
            img_url = urljoin(base_url, img_url)
            
            # Download image if not already downloaded
            if img_url not in self.downloaded_images:
                response = requests.get(img_url, timeout=10)
                response.raise_for_status()
                image_data = response.content
                
                # Detect correct image type
                ext, mime_type = self._get_image_info(image_data)
                
                # Generate unique filename with correct extension
                img_hash = "i" + hashlib.md5(img_url.encode()).hexdigest()
                filename = f'images/{img_hash}{ext}'
                
                # Store image data and add to epub
                self.downloaded_images[img_url] = (filename, image_data)
                
                img = epub.EpubItem(
                    uid=img_hash,
                    file_name=filename,
                    media_type=mime_type,
                    content=image_data
                )
                self.book.add_item(img)
                
            return self.downloaded_images[img_url][0], self.downloaded_images[img_url][1]
            
        except Exception as e:
            logger.error(f"Failed to download image {img_url}: {str(e)}")
            return None, None

    def _process_images(self, content: str, base_url: str) -> str:
        """Process images in content and replace with local references."""
        try:
            root = etree.fromstring(content, parser=etree.HTMLParser())
            
            # Find all img tags
            for img in root.xpath('//img'):
                src = img.get('src')
                if not src:
                    continue
                    
                # Download image and get local filename
                local_file, _ = self._download_image(src, base_url)
                if local_file:
                    img.set('src', local_file)
            
            return etree.tostring(root, encoding='unicode', method='xml')
            
        except Exception as e:
            logger.error(f"Failed to process images: {str(e)}")
            return content

    def create_chapter(self, item: FeedItem) -> epub.EpubHtml:
        """Create EPUB 2.0 compatible chapter from feed item."""
        downloaded = fetch_url(item.link)
        content = extract(
            downloaded,
            output_format="html",
            include_comments=False,
            include_tables=False,
            include_formatting=True,
            include_images=True
        )
        
        if content is None:
            content = "<p>Failed to extract content.</p>"

        # Create XHTML 1.1 compatible header
        header_box = f"""
        <div class="header">
            <h1>{item.title}</h1>
            <p><a href="{item.link}">{item.link}</a></p>
        </div>
        """

        # Process content
        content = content.replace("<graphic", "<img")
        # Wrap content in a div if it's not already wrapped in a block element
        if not re.match(r'^\s*<(div|article|section|main|aside|header|footer|nav|p)\b', content, re.IGNORECASE):
            content = f'<div class="chapter-content">{content}</div>'
        content = header_box + content
        content = self.converter.convert(content)
        content = self._process_images(content, item.link)
        
        # Create EPUB 2.0 compatible chapter
        chapter = epub.EpubHtml(
            title=item.title,
            file_name=f"{slugify(item.title)}.xhtml",
            lang='en'
        )
        chapter.content = content
        
        # Add EPUB 2.0 specific properties
        chapter.properties = []  # Remove EPUB 3 properties
        return chapter
        
    def save(self, chapters: List[epub.EpubHtml], output_path: str):
        """Save EPUB 2.0 book with chapters."""
        # Create and add cover page
        cover = self._create_cover_page()
        self.book.add_item(cover)
        
        # Add chapters
        for chapter in chapters:
            self.book.add_item(chapter)
            
        # Add EPUB 2.0 navigation - only include chapters in TOC
        self.book.toc = [(epub.Section('Items'), chapters)]
        self.book.add_item(epub.EpubNcx())
        
        # Don't add EpubNav() as it's EPUB 3 specific
        
        # Set spine with cover first
        self.book.spine = [cover] + chapters  # Remove 'nav' from spine
        
        # Save book with EPUB 2.0 options
        epub.write_epub(output_path, self.book, {
            'epub2_guide': True,
            'epub3_landmark': False,
            'epub3_pages': False
        })

def create_epub(feed_url: str, item_limit: int = 20) -> str:
    """
    Create an EPUB book from an RSS feed.
    
    Args:
        feed_url: URL of the RSS feed
        item_limit: Maximum number of items to include (default: 20)
        
    Returns:
        Path to the created EPUB file
    """
    try:
        # Parse feed
        parser = RSSFeedParser(feed_url)
        metadata = parser.get_feed_metadata()
        items = parser.get_feed_items(limit=item_limit)
        
        # Log metadata
        logger.info(f"Feed Title: {metadata.title}")
        logger.info(f"Feed Link: {metadata.link}")
        logger.info(f"Feed Description: {metadata.description}")
        
        # Create EPUB
        creator = EPUBCreator(metadata)
        chapters = []
        
        # Process items
        for item in items:
            logger.info(f"Processing: {item.title}")
            chapter = creator.create_chapter(item)
            chapters.append(chapter)
            
        # Save EPUB
        output_path = f"{slugify(metadata.title)}.epub"
        creator.save(chapters, output_path)
        logger.info(f"Successfully created EPUB: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error processing feed: {str(e)}")
        raise
