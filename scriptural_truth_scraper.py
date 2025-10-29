#!/usr/bin/env python3
"""
Scriptural Truth Website Scraper
================================

Comprehensive web scraper for https://scriptural-truth.com/
Downloads all MP3, MP4, PDF files and extracts text content for AI learning.

Based on the website content analysis, this will download:
- MP3 audio files (biblical teachings)
- MP4 video files (video teachings) 
- PDF documents (study materials)
- Web page content (text extraction)
"""

import os
import sys
import json
import time
import requests
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Web scraping dependencies
from bs4 import BeautifulSoup
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Rich for beautiful console output
from rich.console import Console
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()

@dataclass
class MediaFile:
    """Represents a downloadable media file"""
    url: str
    filename: str
    file_type: str
    size: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    page_url: Optional[str] = None

@dataclass
class WebPage:
    """Represents a web page with content"""
    url: str
    title: str
    content: str
    links: List[str] = field(default_factory=list)
    media_files: List[MediaFile] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class ScripturalTruthScraper:
    """Main scraper class for Scriptural Truth website"""
    
    def __init__(self, base_url: str = "https://scriptural-truth.com", output_dir: str = "scriptural-truth-website"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.audio_dir = self.output_dir / "audio"
        self.video_dir = self.output_dir / "video"
        self.pdf_dir = self.output_dir / "pdfs"
        self.pages_dir = self.output_dir / "pages"
        self.metadata_dir = self.output_dir / "metadata"
        
        for dir_path in [self.audio_dir, self.video_dir, self.pdf_dir, self.pages_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Language filtering - only English content
        self.english_only = True
        self.excluded_languages = [
            'spanish', 'french', 'german', 'italian', 'portuguese', 'russian', 
            'chinese', 'japanese', 'korean', 'arabic', 'hindi', 'hebrew',
            'greek', 'latin', 'dutch', 'swedish', 'norwegian', 'danish',
            'finnish', 'polish', 'czech', 'hungarian', 'romanian', 'bulgarian',
            'croatian', 'serbian', 'slovak', 'slovenian', 'estonian', 'latvian',
            'lithuanian', 'ukrainian', 'belarusian', 'macedonian', 'albanian',
            'turkish', 'persian', 'urdu', 'bengali', 'tamil', 'telugu', 'malayalam',
            'kannada', 'gujarati', 'marathi', 'punjabi', 'odia', 'assamese'
        ]
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Track processed URLs to avoid duplicates
        self.processed_urls: Set[str] = set()
        self.downloaded_files: List[MediaFile] = []
        self.scraped_pages: List[WebPage] = []
        
        # File type patterns
        self.media_patterns = {
            'audio': [r'\.mp3$', r'\.wav$', r'\.m4a$'],
            'video': [r'\.mp4$', r'\.avi$', r'\.mov$', r'\.wmv$'],
            'pdf': [r'\.pdf$'],
            'documents': [r'\.doc$', r'\.docx$', r'\.txt$']
        }
    
    def is_english_content(self, url: str, filename: str = None) -> bool:
        """Check if content is in English (not one of the 47 other languages)"""
        if not self.english_only:
            return True
        
        url_lower = url.lower()
        filename_lower = (filename or "").lower()
        
        # Check for language indicators in URL
        for lang in self.excluded_languages:
            if lang in url_lower:
                return False
        
        # Check for language indicators in filename
        for lang in self.excluded_languages:
            if lang in filename_lower:
                return False
        
        # Check for common non-English file patterns
        non_english_patterns = [
            r'[_-](es|fr|de|it|pt|ru|zh|ja|ko|ar|hi|he|el|la|nl|sv|no|da|fi|pl|cs|hu|ro|bg|hr|sr|sk|sl|et|lv|lt|uk|be|mk|sq|tr|fa|ur|bn|ta|te|ml|kn|gu|mr|pa|or|as)[_-]',
            r'[_-](spanish|french|german|italian|portuguese|russian|chinese|japanese|korean|arabic|hindi|hebrew|greek|latin|dutch|swedish|norwegian|danish|finnish|polish|czech|hungarian|romanian|bulgarian|croatian|serbian|slovak|slovenian|estonian|latvian|lithuanian|ukrainian|belarusian|macedonian|albanian|turkish|persian|urdu|bengali|tamil|telugu|malayalam|kannada|gujarati|marathi|punjabi|odia|assamese)[_-]'
        ]
        
        for pattern in non_english_patterns:
            if re.search(pattern, url_lower) or re.search(pattern, filename_lower):
                return False
        
        return True
    
    def should_skip_url(self, url: str) -> bool:
        """Determine if a URL should be skipped based on language filtering"""
        if not self.is_english_content(url):
            console.print(f"🚫 Skipping non-English content: {url}")
            return True
        
        # Skip common non-English directories
        skip_patterns = [
            r'/languages?/',
            r'/translations?/',
            r'/multilingual/',
            r'/international/',
            r'/[a-z]{2}/',  # Two-letter language codes
            r'/[a-z]{2}-[a-z]{2}/',  # Language-region codes
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url.lower()):
                console.print(f"🚫 Skipping language directory: {url}")
                return True
        
        return False
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page"""
        try:
            console.print(f"📄 Fetching: {url}")
            response = self.session.get(url, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
            
        except Exception as e:
            console.print(f"❌ Error fetching {url}: {e}")
            return None
    
    def extract_media_links(self, soup: BeautifulSoup, page_url: str) -> List[MediaFile]:
        """Extract all media file links from a page"""
        media_files = []
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            if not href:
                continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(page_url, href)
            
            # Skip non-English content
            if self.should_skip_url(full_url):
                continue
            
            # Check if it's a media file
            for file_type, patterns in self.media_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, full_url, re.IGNORECASE):
                        filename = self.clean_filename(Path(urlparse(full_url).path).name)
                        if not filename:
                            continue
                        
                        # Double-check filename for English content
                        if not self.is_english_content(full_url, filename):
                            console.print(f"🚫 Skipping non-English file: {filename}")
                            continue
                        
                        media_file = MediaFile(
                            url=full_url,
                            filename=filename,
                            file_type=file_type,
                            title=link.get_text(strip=True) or filename,
                            page_url=page_url
                        )
                        media_files.append(media_file)
                        break
        
        # Also check for embedded media (audio, video tags)
        for tag in soup.find_all(['audio', 'video']):
            src = tag.get('src')
            if src:
                full_url = urljoin(page_url, src)
                filename = self.clean_filename(Path(urlparse(full_url).path).name)
                if filename:
                    file_type = 'audio' if tag.name == 'audio' else 'video'
                    media_file = MediaFile(
                        url=full_url,
                        filename=filename,
                        file_type=file_type,
                        title=tag.get('title') or filename,
                        page_url=page_url
                    )
                    media_files.append(media_file)
        
        return media_files
    
    def clean_filename(self, filename: str) -> str:
        """Clean filename for safe storage"""
        if not filename:
            return ""
        
        # Decode URL encoding
        filename = unquote(filename)
        
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove extra spaces and dots
        filename = re.sub(r'\s+', ' ', filename).strip()
        filename = filename.strip('.')
        
        return filename
    
    def download_file(self, media_file: MediaFile) -> bool:
        """Download a media file"""
        try:
            # Determine target directory
            if media_file.file_type == 'audio':
                target_dir = self.audio_dir
            elif media_file.file_type == 'video':
                target_dir = self.video_dir
            elif media_file.file_type == 'pdf':
                target_dir = self.pdf_dir
            else:
                target_dir = self.output_dir / "other"
                target_dir.mkdir(exist_ok=True)
            
            target_path = target_dir / media_file.filename
            
            # Skip if already downloaded
            if target_path.exists():
                console.print(f"⏭️  Skipping existing file: {media_file.filename}")
                return True
            
            console.print(f"⬇️  Downloading: {media_file.filename}")
            
            response = self.session.get(media_file.url, stream=True, timeout=60, verify=False)
            response.raise_for_status()
            
            # Get file size if available
            content_length = response.headers.get('content-length')
            if content_length:
                media_file.size = int(content_length)
            
            # Download file
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            console.print(f"✅ Downloaded: {media_file.filename}")
            return True
            
        except Exception as e:
            console.print(f"❌ Error downloading {media_file.filename}: {e}")
            return False
    
    def extract_page_content(self, soup: BeautifulSoup, url: str) -> WebPage:
        """Extract text content from a web page"""
        # Get title
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if main_content:
            content = main_content.get_text(separator='\n', strip=True)
        else:
            content = soup.get_text(separator='\n', strip=True)
        
        # Clean up content
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = content.strip()
        
        # Extract all links (English only)
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                full_url = urljoin(url, href)
                if (full_url.startswith(self.base_url) and 
                    not self.should_skip_url(full_url)):
                    links.append(full_url)
        
        # Extract media files
        media_files = self.extract_media_links(soup, url)
        
        return WebPage(
            url=url,
            title=title,
            content=content,
            links=links,
            media_files=media_files
        )
    
    def save_page_content(self, page: WebPage) -> None:
        """Save page content to file"""
        try:
            # Create filename from URL
            url_path = urlparse(page.url).path
            if url_path == '/' or url_path == '':
                filename = 'index.html'
            else:
                filename = url_path.replace('/', '_').strip('_') + '.html'
            
            filename = self.clean_filename(filename)
            if not filename.endswith('.html'):
                filename += '.html'
            
            # Save HTML content
            html_path = self.pages_dir / filename
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(f"<!-- {page.title} -->\n")
                f.write(f"<!-- URL: {page.url} -->\n")
                f.write(f"<!-- Scraped: {page.timestamp} -->\n\n")
                f.write(page.content)
            
            # Save text content
            txt_path = self.pages_dir / (filename.replace('.html', '.txt'))
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"Title: {page.title}\n")
                f.write(f"URL: {page.url}\n")
                f.write(f"Scraped: {page.timestamp}\n")
                f.write("=" * 50 + "\n\n")
                f.write(page.content)
            
            console.print(f"💾 Saved page: {filename}")
            
        except Exception as e:
            console.print(f"❌ Error saving page {page.url}: {e}")
    
    def discover_all_pages(self, start_url: str) -> List[str]:
        """Discover all pages on the website"""
        console.print("🔍 Discovering all pages on the website...")
        
        urls_to_visit = [start_url]
        discovered_urls = set()
        
        with Progress(
            TextColumn("[bold blue]Discovering pages"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Discovering", total=None)
            
            while urls_to_visit:
                current_url = urls_to_visit.pop(0)
                
                if current_url in discovered_urls or current_url in self.processed_urls:
                    continue
                
                discovered_urls.add(current_url)
                progress.update(task, description=f"Processing {current_url}")
                
                soup = self.get_page_content(current_url)
                if not soup:
                    continue
                
                # Extract links from this page
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(current_url, href)
                        if (full_url.startswith(self.base_url) and 
                            full_url not in discovered_urls and 
                            full_url not in self.processed_urls and
                            not self.should_skip_url(full_url)):
                            urls_to_visit.append(full_url)
                
                time.sleep(0.5)  # Be respectful to the server
        
        return list(discovered_urls)
    
    def scrape_website(self, start_url: str = None) -> None:
        """Main scraping function"""
        if start_url is None:
            start_url = self.base_url
        
        console.print(f"🌐 Starting scrape of {self.base_url}")
        console.print(f"📁 Output directory: {self.output_dir}")
        
        # Discover all pages
        all_urls = self.discover_all_pages(start_url)
        console.print(f"📊 Found {len(all_urls)} pages to process")
        
        # Process each page
        with Progress(
            TextColumn("[bold blue]Scraping pages"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Scraping", total=len(all_urls))
            
            for url in all_urls:
                progress.update(task, description=f"Processing {url}")
                
                soup = self.get_page_content(url)
                if not soup:
                    progress.advance(task)
                    continue
                
                # Extract page content
                page = self.extract_page_content(soup, url)
                self.scraped_pages.append(page)
                
                # Save page content
                self.save_page_content(page)
                
                # Download media files
                for media_file in page.media_files:
                    if self.download_file(media_file):
                        self.downloaded_files.append(media_file)
                
                self.processed_urls.add(url)
                progress.advance(task)
                
                time.sleep(1)  # Be respectful to the server
        
        # Save metadata
        self.save_metadata()
        
        # Display summary
        self.display_summary()
    
    def save_metadata(self) -> None:
        """Save scraping metadata"""
        metadata = {
            "scrape_info": {
                "base_url": self.base_url,
                "scrape_date": datetime.now().isoformat(),
                "total_pages": len(self.scraped_pages),
                "total_files": len(self.downloaded_files)
            },
            "pages": [
                {
                    "url": page.url,
                    "title": page.title,
                    "timestamp": page.timestamp,
                    "content_length": len(page.content),
                    "media_count": len(page.media_files)
                }
                for page in self.scraped_pages
            ],
            "files": [
                {
                    "url": file.url,
                    "filename": file.filename,
                    "file_type": file.file_type,
                    "size": file.size,
                    "title": file.title,
                    "page_url": file.page_url
                }
                for file in self.downloaded_files
            ]
        }
        
        metadata_path = self.metadata_dir / "scrape_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        console.print(f"💾 Saved metadata to {metadata_path}")
    
    def display_summary(self) -> None:
        """Display scraping summary"""
        # Count files by type
        file_counts = {}
        total_size = 0
        
        for file in self.downloaded_files:
            file_type = file.file_type
            file_counts[file_type] = file_counts.get(file_type, 0) + 1
            if file.size:
                total_size += file.size
        
        # Create summary table
        table = Table(title="Scriptural Truth Scraping Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")
        
        table.add_row("Total Pages Scraped", str(len(self.scraped_pages)))
        table.add_row("Total Files Downloaded", str(len(self.downloaded_files)))
        
        for file_type, count in file_counts.items():
            table.add_row(f"{file_type.title()} Files", str(count))
        
        if total_size > 0:
            size_mb = total_size / (1024 * 1024)
            table.add_row("Total Size", f"{size_mb:.2f} MB")
        
        console.print(table)
        
        # Display directory structure
        console.print("\n📁 Directory Structure:")
        console.print(f"  📂 {self.output_dir}")
        console.print(f"    📂 audio/ - {file_counts.get('audio', 0)} MP3 files")
        console.print(f"    📂 video/ - {file_counts.get('video', 0)} MP4 files")
        console.print(f"    📂 pdfs/ - {file_counts.get('pdf', 0)} PDF files")
        console.print(f"    📂 pages/ - {len(self.scraped_pages)} web pages")
        console.print(f"    📂 metadata/ - Scraping metadata")

def main():
    """Main function"""
    console.print("🌐 Scriptural Truth Website Scraper")
    console.print("===================================")
    
    # Initialize scraper
    scraper = ScripturalTruthScraper()
    
    try:
        # Start scraping
        scraper.scrape_website()
        
        console.print("\n🎉 Scraping completed successfully!")
        console.print("📖 All content is now ready for AI learning integration")
        
    except KeyboardInterrupt:
        console.print("\n⏹️  Scraping interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Scraping failed: {e}")
        logger.exception("Scraping error")

if __name__ == "__main__":
    main()
