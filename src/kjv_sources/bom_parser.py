#!/usr/bin/env python3
"""
Book of Mormon Parser
=====================

Parses Book of Mormon JSON data into the same verse-level structure as Torah data,
enabling comparative analysis and vector database integration.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import Counter

# Book of Mormon author attribution
BOOK_AUTHORS = {
    "1 Nephi": "Nephi",
    "2 Nephi": "Nephi",
    "Jacob": "Jacob",
    "Enos": "Enos",
    "Jarom": "Jarom",
    "Omni": "Omni",
    "Words of Mormon": "Mormon",
    "Mosiah": "Mormon",  # Abridged by Mormon
    "Alma": "Mormon",     # Abridged by Mormon (original by Alma)
    "Helaman": "Mormon",  # Abridged by Mormon
    "3 Nephi": "Mormon",  # Abridged by Mormon
    "4 Nephi": "Mormon",  # Abridged by Mormon
    "Mormon": "Mormon",
    "Ether": "Moroni",    # Abridged by Moroni from Jaredite records
    "Moroni": "Moroni"
}

# Literary style classification
LITERARY_STYLES = {
    "1 Nephi": "narrative",
    "2 Nephi": "prophetic",
    "Jacob": "prophetic",
    "Enos": "personal",
    "Jarom": "personal",
    "Omni": "personal",
    "Words of Mormon": "editorial",
    "Mosiah": "narrative",
    "Alma": "doctrinal",
    "Helaman": "narrative",
    "3 Nephi": "christ_ministry",
    "4 Nephi": "historical",
    "Mormon": "prophetic",
    "Ether": "narrative",
    "Moroni": "doctrinal"
}

# Isaiah chapters referenced in Book of Mormon
ISAIAH_PARALLELS = {
    # 2 Nephi contains many Isaiah chapters
    "2 Nephi 12": "Isaiah 2",
    "2 Nephi 13": "Isaiah 3",
    "2 Nephi 14": "Isaiah 4",
    "2 Nephi 15": "Isaiah 5",
    "2 Nephi 16": "Isaiah 6",
    "2 Nephi 17": "Isaiah 7",
    "2 Nephi 18": "Isaiah 8",
    "2 Nephi 19": "Isaiah 9",
    "2 Nephi 20": "Isaiah 10",
    "2 Nephi 21": "Isaiah 11",
    "2 Nephi 22": "Isaiah 12",
    "2 Nephi 23": "Isaiah 13",
    "2 Nephi 24": "Isaiah 14",
    # Add more as needed
}

# Book order for canonical ordering
BOOK_ORDER = [
    "1 Nephi", "2 Nephi", "Jacob", "Enos", "Jarom", "Omni",
    "Words of Mormon", "Mosiah", "Alma", "Helaman", "3 Nephi",
    "4 Nephi", "Mormon", "Ether", "Moroni"
]

BOOK_INDEX = {book: idx for idx, book in enumerate(BOOK_ORDER)}


@dataclass
class BookOfMormonVerse:
    """Structured representation of a Book of Mormon verse"""
    canonical_reference: str
    full_text: str
    book: str
    chapter: int
    verse: int
    book_category: str = "book_of_mormon"
    author: str = ""
    literary_style: str = ""
    isaiah_parallel: Optional[str] = None
    christ_reference: bool = False
    canonical_order: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV/JSON export"""
        return asdict(self)


class BookOfMormonParser:
    """Parse Book of Mormon JSON into structured verse data"""
    
    def __init__(self, json_path: Path):
        self.json_path = Path(json_path)
        self.verses: List[BookOfMormonVerse] = []
        
    def parse(self) -> List[BookOfMormonVerse]:
        """Parse the JSON file and return list of verse objects"""
        print(f"[INFO] Parsing Book of Mormon from {self.json_path}")
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for book_data in data.get("books", []):
            book_name = book_data.get("book")
            author = BOOK_AUTHORS.get(book_name, "Unknown")
            literary_style = LITERARY_STYLES.get(book_name, "narrative")
            
            for chapter_data in book_data.get("chapters", []):
                chapter_num = chapter_data.get("chapter")
                
                for verse_data in chapter_data.get("verses", []):
                    verse_num = verse_data.get("verse")
                    text = verse_data.get("text", "")
                    reference = verse_data.get("reference", f"{book_name} {chapter_num}:{verse_num}")
                    
                    # Check for Isaiah parallel
                    chapter_ref = f"{book_name} {chapter_num}"
                    isaiah_parallel = ISAIAH_PARALLELS.get(chapter_ref)
                    
                    # Check for Christ references (simple keyword detection)
                    christ_reference = self._contains_christ_reference(text)
                    
                    # Calculate canonical order
                    book_idx = BOOK_INDEX.get(book_name, 999)
                    canonical_order = book_idx * 100000 + chapter_num * 1000 + verse_num
                    
                    verse = BookOfMormonVerse(
                        canonical_reference=reference,
                        full_text=text,
                        book=book_name,
                        chapter=chapter_num,
                        verse=verse_num,
                        book_category="book_of_mormon",
                        author=author,
                        literary_style=literary_style,
                        isaiah_parallel=isaiah_parallel,
                        christ_reference=christ_reference,
                        canonical_order=canonical_order
                    )
                    
                    self.verses.append(verse)
        
        print(f"[INFO] Parsed {len(self.verses)} verses from {len(BOOK_ORDER)} books")
        return self.verses
    
    def _contains_christ_reference(self, text: str) -> bool:
        """Check if verse contains references to Christ/Messiah"""
        text_lower = text.lower()
        keywords = [
            "christ", "jesus", "messiah", "redeemer", "savior", "saviour",
            "lamb of god", "son of god", "holy one", "lord god omnipotent"
        ]
        return any(keyword in text_lower for keyword in keywords)
    
    def export_to_csv(self, output_path: Path):
        """Export parsed verses to CSV file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'canonical_reference', 'full_text', 'book', 'chapter', 'verse',
            'book_category', 'author', 'literary_style', 'isaiah_parallel',
            'christ_reference', 'canonical_order'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for verse in self.verses:
                writer.writerow(verse.to_dict())
        
        print(f"[INFO] Exported {len(self.verses)} verses to {output_path}")
    
    def export_to_jsonl(self, output_path: Path):
        """Export parsed verses to JSONL file (for embedding/training)"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for verse in self.verses:
                f.write(json.dumps(verse.to_dict()) + '\n')
        
        print(f"[INFO] Exported {len(self.verses)} verses to {output_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        if not self.verses:
            return {}
        
        books = set(v.book for v in self.verses)
        authors = Counter(v.author for v in self.verses)
        styles = Counter(v.literary_style for v in self.verses)
        christ_refs = sum(1 for v in self.verses if v.christ_reference)
        isaiah_refs = sum(1 for v in self.verses if v.isaiah_parallel)
        
        return {
            "total_verses": len(self.verses),
            "total_books": len(books),
            "books": sorted(books, key=lambda b: BOOK_INDEX.get(b, 999)),
            "authors": dict(authors),
            "literary_styles": dict(styles),
            "christ_references": christ_refs,
            "isaiah_parallels": isaiah_refs,
            "avg_verse_length": sum(len(v.full_text) for v in self.verses) / len(self.verses)
        }


def main():
    """Main entry point for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse Book of Mormon JSON")
    parser.add_argument(
        "--input",
        default="book_of_mormon_raw.json",
        help="Input JSON file path"
    )
    parser.add_argument(
        "--output-csv",
        default="output/book_of_mormon.csv",
        help="Output CSV file path"
    )
    parser.add_argument(
        "--output-jsonl",
        default="output/book_of_mormon.jsonl",
        help="Output JSONL file path"
    )
    
    args = parser.parse_args()
    
    # Parse
    bom_parser = BookOfMormonParser(Path(args.input))
    verses = bom_parser.parse()
    
    # Export
    bom_parser.export_to_csv(Path(args.output_csv))
    bom_parser.export_to_jsonl(Path(args.output_jsonl))
    
    # Print statistics
    stats = bom_parser.get_statistics()
    print("\n=== Book of Mormon Statistics ===")
    print(f"Total verses: {stats['total_verses']}")
    print(f"Total books: {stats['total_books']}")
    print(f"Christ references: {stats['christ_references']}")
    print(f"Isaiah parallels: {stats['isaiah_parallels']}")
    print(f"Average verse length: {stats['avg_verse_length']:.1f} characters")
    print(f"\nAuthors: {stats['authors']}")
    print(f"\nLiterary styles: {stats['literary_styles']}")


if __name__ == "__main__":
    main()

