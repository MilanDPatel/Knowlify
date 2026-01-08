import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

class ManimExamplesScraper:
    def __init__(self):
        self.url = "https://docs.manim.community/en/stable/examples.html"
        self.output_dir = Path("manim_examples")
        self.output_dir.mkdir(exist_ok=True)
        self.animation_count = 0
        
    def get_page(self):
        """Fetch the examples page"""
        try:
            print(f"Fetching: {self.url}")
            response = requests.get(self.url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching page: {e}")
            return None
    
    def extract_category_from_heading(self, code_element):
        """Find the category heading above the code block"""
        current = code_element
        
        # Walk backwards to find heading
        for _ in range(20):
            current = current.find_previous()
            if not current:
                break
            
            # Check for h2 or h3 headings (category names)
            if current.name in ['h2', 'h3']:
                heading_text = current.get_text().strip()
                # Clean up heading (remove special characters, make folder-safe)
                category = re.sub(r'[^\w\s-]', '', heading_text)
                category = re.sub(r'\s+', '_', category).lower()
                return category
        
        return "general"
    
    def extract_all_examples(self, html):
        """Extract all code examples from the page"""
        soup = BeautifulSoup(html, 'html.parser')
        examples = []
        
        # Find all code blocks
        code_containers = []
        code_containers.extend(soup.find_all('div', class_=re.compile(r'highlight')))
        code_containers.extend(soup.find_all('pre', class_='literal-block'))
        
        seen_code = set()
        
        for container in code_containers:
            # Get the code element
            code_elem = container.find('code') or container.find('pre') or container
            if not code_elem:
                continue
            
            # Extract text preserving formatting
            code_text = code_elem.get_text().strip()
            
            # Skip if empty, too short, or duplicate
            if not code_text or len(code_text) < 20 or code_text in seen_code:
                continue
            
            # Only include Manim code
            if not self.is_manim_code(code_text):
                continue
            
            seen_code.add(code_text)
            
            # Get category from heading
            category = self.extract_category_from_heading(container)
            
            # Get class name if available
            class_name = self.extract_class_name(code_text)
            
            examples.append({
                'code_lines': code_text.split('\n'),
                'source_url': self.url,
                'category': category,
                'class_name': class_name
            })
        
        return examples
    
    def is_manim_code(self, code):
        """Check if code is Manim-related"""
        # Strong indicators
        strong_indicators = [
            r'from manim import',
            r'import manim',
            r'class\s+\w+\s*\(\s*Scene',
            r'class\s+\w+\s*\(\s*ThreeDScene',
            r'class\s+\w+\s*\(\s*MovingCameraScene',
        ]
        
        for indicator in strong_indicators:
            if re.search(indicator, code, re.IGNORECASE):
                return True
        
        # Multiple weak indicators
        weak_indicators = [
            r'def construct\s*\(',
            r'self\.play\s*\(',
            r'self\.add\s*\(',
            r'self\.wait\s*\(',
            r'Circle\s*\(',
            r'Square\s*\(',
            r'Text\s*\(',
            r'MathTex\s*\(',
            r'Create\s*\(',
            r'FadeIn\s*\(',
        ]
        
        matches = sum(1 for indicator in weak_indicators if re.search(indicator, code))
        return matches >= 3
    
    def extract_class_name(self, code):
        """Extract the Scene class name from code"""
        match = re.search(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\)', code)
        if match:
            return match.group(1)
        return None
    
    def save_example(self, example_data):
        """Save example as JSON with folder structure"""
        self.animation_count += 1
        
        # Create category folder
        category = example_data['category']
        category_path = self.output_dir / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        # Create filename based on class name or counter
        if example_data['class_name']:
            base_name = example_data['class_name']
        else:
            base_name = f"example_{self.animation_count}"
        
        filename = f"{base_name}.json"
        filepath = category_path / filename
        
        # Handle duplicate filenames
        counter = 1
        while filepath.exists():
            filename = f"{base_name}_{counter}.json"
            filepath = category_path / filename
            counter += 1
        
        # Save JSON
        json_data = {
            "code": example_data['code_lines'],
            "source_url": example_data['source_url']
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Show relative path
        rel_path = filepath.relative_to(self.output_dir)
        print(f"  ✓ Saved: {rel_path}")
    
    def scrape(self):
        """Main scraping method"""
        print("="*60)
        print("Manim Examples Page Scraper")
        print("="*60)
        print(f"URL: {self.url}")
        print(f"Output: {self.output_dir.absolute()}\n")
        
        # Get the page
        html = self.get_page()
        if not html:
            print("Failed to fetch page!")
            return
        
        # Extract all examples
        print("Extracting code examples...")
        examples = self.extract_all_examples(html)
        print(f"Found {len(examples)} code examples\n")
        
        # Save each example
        for example in examples:
            self.save_example(example)
        
        # Summary
        print("\n" + "="*60)
        print(f"✓ Scraping Complete!")
        print(f"  Total examples: {len(examples)}")
        print(f"  Output directory: {self.output_dir.absolute()}")
        
        # Count by category
        categories = {}
        for example in examples:
            cat = example['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n  Examples by category:")
        for cat, count in sorted(categories.items()):
            print(f"    - {cat}: {count}")
        
        print("="*60)
        
        # Save summary
        summary = {
            'total_examples': len(examples),
            'source_url': self.url,
            'categories': categories
        }
        with open(self.output_dir / '_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

if __name__ == "__main__":
    scraper = ManimExamplesScraper()
    scraper.scrape()