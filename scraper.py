#!/usr/bin/env python3
"""
Scraper for AMC problems from Art of Problem Solving wiki.
Extracts problems, solutions, and images, preserving structure for HTML recreation.
Supports AMC 8, AMC 10A, and AMC 10B.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time

BASE_URL = "https://artofproblemsolving.com"

class AMCScraper:
    def __init__(self, contest_type, year, base_output_dir="data"):
        """
        Initialize scraper for a specific contest type and year.
        
        Args:
            contest_type: One of "AMC8", "AMC10A", "AMC10B"
            year: Year as integer (e.g., 2025, 2024, etc.)
            base_output_dir: Base directory for output (default: "data")
        """
        self.contest_type = contest_type
        self.year = year
        self.base_output_dir = Path(base_output_dir)
        
        # Determine directory structure based on contest type
        if contest_type == "AMC8":
            self.contest_name = "AMC 8"
            self.dir_name = "AMC8"
        elif contest_type == "AMC10A":
            self.contest_name = "AMC 10A"
            self.dir_name = "AMC10A"
        elif contest_type == "AMC10B":
            self.contest_name = "AMC 10B"
            self.dir_name = "AMC10B"
        elif contest_type == "AMC12A":
            self.contest_name = "AMC 12A"
            self.dir_name = "AMC12A"
        elif contest_type == "AMC12B":
            self.contest_name = "AMC 12B"
            self.dir_name = "AMC12B"
        else:
            raise ValueError(f"Unknown contest type: {contest_type}")
        
        # Structure: data/CONTEST_TYPE/YEAR/
        self.output_dir = self.base_output_dir / self.dir_name / str(year)
        self.images_dir = self.output_dir / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def fetch_page(self, url):
        """Fetch a page and return BeautifulSoup object."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def download_image(self, img_url, problem_num, img_type="problem"):
        """Download an image and return local path."""
        try:
            # Handle relative URLs
            if not img_url.startswith('http'):
                img_url = urljoin(BASE_URL, img_url)
            
            response = self.session.get(img_url, timeout=30)
            response.raise_for_status()
            
            # Determine file extension
            parsed = urlparse(img_url)
            ext = os.path.splitext(parsed.path)[1] or '.png'
            
            # Create filename
            filename = f"problem_{problem_num}_{img_type}_{hash(img_url) % 10000}{ext}"
            filepath = self.images_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return f"images/{filename}"
        except Exception as e:
            print(f"Error downloading image {img_url}: {e}")
            return None
    
    def get_main_page_url(self):
        """Get the main page URL for this contest type and year."""
        if self.contest_type == "AMC8":
            return f"{BASE_URL}/wiki/index.php/{self.year}_AMC_8"
        elif self.contest_type == "AMC10A":
            return f"{BASE_URL}/wiki/index.php/{self.year}_AMC_10A"
        elif self.contest_type == "AMC10B":
            return f"{BASE_URL}/wiki/index.php/{self.year}_AMC_10B"
        elif self.contest_type == "AMC12A":
            return f"{BASE_URL}/wiki/index.php/{self.year}_AMC_12A"
        elif self.contest_type == "AMC12B":
            return f"{BASE_URL}/wiki/index.php/{self.year}_AMC_12B"
    
    def extract_content_with_images(self, element, problem_num, img_type="problem"):
        """Extract content preserving order of text and images."""
        content = []
        
        if element is None:
            return content
        
        # Handle string content directly
        if isinstance(element, str):
            text = element.strip()
            if text:
                content.append({"type": "text", "content": text})
            return content
        
        # Process all children to preserve order
        for child in element.children:
            if isinstance(child, str):
                text = child.strip()
                if text:
                    content.append({"type": "text", "content": text})
            elif hasattr(child, 'name'):
                if child.name == 'img':
                    # Extract image
                    img_src = child.get('src') or child.get('data-src')
                    if img_src:
                        local_path = self.download_image(img_src, problem_num, img_type)
                        if local_path:
                            content.append({
                                "type": "image",
                                "src": img_src,
                                "local_path": local_path,
                                "alt": child.get('alt', ''),
                                "width": child.get('width'),
                                "height": child.get('height')
                            })
                elif child.name == 'a' and child.find('img'):
                    # Image wrapped in link
                    img = child.find('img')
                    img_src = img.get('src') or img.get('data-src')
                    if img_src:
                        local_path = self.download_image(img_src, problem_num, img_type)
                        if local_path:
                            content.append({
                                "type": "image",
                                "src": img_src,
                                "local_path": local_path,
                                "alt": img.get('alt', ''),
                                "width": img.get('width'),
                                "height": img.get('height')
                            })
                elif child.name in ['p', 'div', 'span', 'br', 'pre', 'code']:
                    # Recursively process nested elements
                    nested = self.extract_content_with_images(child, problem_num, img_type)
                    if nested:
                        content.extend(nested)
                elif child.name == 'br':
                    content.append({"type": "line_break"})
                else:
                    # For other elements, get text content and preserve HTML if needed
                    text = child.get_text(strip=True)
                    if text:
                        # Preserve the HTML structure for complex elements
                        html_str = str(child)
                        content.append({
                            "type": "html",
                            "content": text,
                            "html": html_str,
                            "tag": child.name
                        })
        
        return content
    
    def extract_problem(self, soup, problem_num):
        """Extract problem statement, images, and answer choices."""
        problem_data = {
            "number": problem_num,
            "content": [],
            "answer_choices": []
        }
        
        # Find the Problem section - AoPS wiki uses span with id="Problem"
        problem_heading = soup.find('span', {'id': 'Problem'})
        if not problem_heading:
            # Try finding by heading text
            for heading in soup.find_all(['h2', 'h3', 'span']):
                text = heading.get_text().strip().lower()
                if text == 'problem' or (heading.name == 'span' and heading.get('id') == 'Problem'):
                    problem_heading = heading
                    break
        
        if problem_heading:
            # Find the parent container (usually a div or the main content area)
            # Get all content until we hit Solution section
            current = problem_heading.parent if problem_heading.parent else problem_heading
            if current.name != 'div':
                current = current.find_next_sibling()
            else:
                # Start from after the heading
                current = problem_heading.find_next_sibling()
            
            problem_content = []
            
            while current:
                if current.name in ['h2', 'h3']:
                    text = current.get_text().strip().lower()
                    if 'solution' in text or 'see also' in text or 'video solution' in text:
                        break
                
                # Also check for span with id starting with "Solution"
                if current.name == 'span' and current.get('id'):
                    if current.get('id').startswith('Solution'):
                        break
                
                problem_content.append(current)
                current = current.find_next_sibling()
            
            # Extract content from problem section
            for elem in problem_content:
                content = self.extract_content_with_images(elem, problem_num, "problem")
                if content:
                    problem_data["content"].extend(content)
            
            # Extract answer choices (usually in format like $\textbf{(A)}\ ...$)
            # First try from text content
            problem_text_parts = []
            for item in problem_data['content']:
                if item['type'] == 'text':
                    problem_text_parts.append(item['content'])
                elif item['type'] == 'html':
                    problem_text_parts.append(item['content'])
            
            problem_text = ' '.join(problem_text_parts)
            
            # Match LaTeX answer choices: $\textbf{(A)}\ ...$ or similar patterns
            answer_patterns = [
                r'\$\\textbf\{\(([A-E])\)\}\\s*([^\$]+?)(?=\$|\\qquad|$)',
                r'\\textbf\{\(([A-E])\)\}\\s*([^\$]+?)(?=\$|\\qquad|$)',
                r'\(([A-E])\)\s*([^\$]+?)(?=\$|\\qquad|$)',
            ]
            
            found_choices = False
            for pattern in answer_patterns:
                matches = re.findall(pattern, problem_text)
                if matches:
                    for letter, text in matches:
                        # Clean up the text
                        text = re.sub(r'\$+', '', text).strip()
                        if text and len(text) > 0:
                            problem_data["answer_choices"].append({
                                "letter": letter,
                                "text": text.strip()
                            })
                    found_choices = True
                    break
            
            # If not found in text, try extracting from image alt text
            if not found_choices:
                for item in problem_data['content']:
                    if item['type'] == 'image' and item.get('alt'):
                        alt_text = item['alt']
                        # Check if alt text contains answer choices pattern
                        if '\\textbf{(A)}' in alt_text or 'textbf{(A)}' in alt_text:
                            # Extract all answer choices from alt text
                            # Pattern: \textbf{(X)}\ ... \qquad or end of string
                            # Match each choice separately
                            for letter in ['A', 'B', 'C', 'D', 'E']:
                                # Pattern for each choice: \textbf{(X)}\ ... followed by \qquad or end
                                pattern = rf'\\textbf\{{\({letter}\)\}}\\s*([^\\]+?)(?=\\qquad|\\textbf|$)'
                                match = re.search(pattern, alt_text)
                                if match:
                                    text = match.group(1)
                                    # Clean up LaTeX commands and extra spaces
                                    text = re.sub(r'\\[a-zA-Z]+\{?\}?', '', text).strip()
                                    text = re.sub(r'\s+', ' ', text).strip()
                                    # Remove trailing $ signs and whitespace
                                    text = re.sub(r'\$+\s*$', '', text).strip()
                                    if text:
                                        problem_data["answer_choices"].append({
                                            "letter": letter,
                                            "text": text,
                                            "source": "image_alt"
                                        })
                            
                            if problem_data["answer_choices"]:
                                break
        
        return problem_data
    
    def extract_solutions(self, soup, problem_num, max_solutions=3):
        """Extract up to max_solutions solutions."""
        solutions = []
        
        # Find all solution sections
        for i in range(1, max_solutions + 1):
            solution_id = f"Solution_{i}"
            # Find span with the solution ID
            solution_span = soup.find('span', {'id': solution_id})
            
            if not solution_span:
                break
            
            # Get the parent h2 element (solutions are in h2 tags)
            solution_heading = solution_span.parent if solution_span.parent and solution_span.parent.name == 'h2' else None
            
            if not solution_heading:
                # Try finding by text pattern in headings
                for heading in soup.find_all(['h2', 'h3']):
                    text = heading.get_text().strip()
                    if text == f"Solution {i}" or text == f"Solution {i}:":
                        solution_heading = heading
                        break
            
            if not solution_heading:
                break
            
            solution_data = {
                "number": i,
                "content": []
            }
            
            # Get content until next solution or section
            # Start from the next sibling of the h2 element
            current = solution_heading.find_next_sibling()
            while current:
                # Check if we've hit the next section
                if current.name == 'h2':
                    # Check if it's another solution heading
                    span = current.find('span', id=True)
                    if span:
                        span_id = span.get('id', '')
                        if span_id.startswith('Solution_'):
                            # Check if it's the next solution
                            next_num_match = re.search(r'Solution_(\d+)', span_id)
                            if next_num_match:
                                next_num = int(next_num_match.group(1))
                                if next_num == i + 1:
                                    break
                        elif span_id.startswith('Video') or span_id.startswith('See_Also'):
                            break
                    else:
                        # Check text content
                        text = current.get_text().strip().lower()
                        if text.startswith('solution') and i < max_solutions:
                            next_num_match = re.search(r'solution\s+(\d+)', text, re.IGNORECASE)
                            if next_num_match:
                                next_num = int(next_num_match.group(1))
                                if next_num == i + 1:
                                    break
                        elif text.startswith('video') or text.startswith('see also'):
                            break
                
                content = self.extract_content_with_images(current, problem_num, f"solution_{i}")
                if content:
                    solution_data["content"].extend(content)
                current = current.find_next_sibling()
            
            if solution_data["content"]:
                solutions.append(solution_data)
        
        return solutions
    
    def scrape_problem(self, problem_url, problem_num):
        """Scrape a single problem page."""
        print(f"  Scraping Problem {problem_num}...")
        soup = self.fetch_page(problem_url)
        
        if not soup:
            return None
        
        problem_data = self.extract_problem(soup, problem_num)
        solutions = self.extract_solutions(soup, problem_num, max_solutions=3)
        problem_data["solutions"] = solutions
        problem_data["year"] = self.year
        problem_data["contest_type"] = self.contest_type
        problem_data["contest_name"] = self.contest_name
        
        return problem_data
    
    def get_problem_links(self):
        """Get all problem links from the main page."""
        main_page_url = self.get_main_page_url()
        soup = self.fetch_page(main_page_url)
        if not soup:
            return []
        
        links = []
        # Find the answer key section or problem links
        # Problems are typically linked as "Problem 1", "Problem 2", etc.
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()
            
            # Match pattern like "Problem 1", "Problem 2", etc.
            match = re.match(r'Problem\s+(\d+)', text, re.IGNORECASE)
            if match:
                problem_num = int(match.group(1))
                if 1 <= problem_num <= 25:
                    full_url = urljoin(BASE_URL, href)
                    links.append((problem_num, full_url))
        
        # Remove duplicates and sort
        links = sorted(set(links), key=lambda x: x[0])
        
        # If no links found, try constructing URLs directly
        if not links:
            print(f"No problem links found on main page. Constructing URLs directly...")
            for i in range(1, 26):
                if self.contest_type == "AMC8":
                    url = f"{BASE_URL}/wiki/index.php?title={self.year}_AMC_8_Problems/Problem_{i}"
                elif self.contest_type == "AMC10A":
                    url = f"{BASE_URL}/wiki/index.php?title={self.year}_AMC_10A_Problems/Problem_{i}"
                elif self.contest_type == "AMC10B":
                    url = f"{BASE_URL}/wiki/index.php?title={self.year}_AMC_10B_Problems/Problem_{i}"
                elif self.contest_type == "AMC12A":
                    url = f"{BASE_URL}/wiki/index.php?title={self.year}_AMC_12A_Problems/Problem_{i}"
                elif self.contest_type == "AMC12B":
                    url = f"{BASE_URL}/wiki/index.php?title={self.year}_AMC_12B_Problems/Problem_{i}"
                links.append((i, url))
        
        return links
    
    def scrape_all(self):
        """Scrape all 25 problems for this contest type and year."""
        print(f"\n{'='*60}")
        print(f"Scraping {self.year} {self.contest_name} Problems")
        print(f"{'='*60}")
        print("Fetching problem links...")
        problem_links = self.get_problem_links()
        
        print(f"Found {len(problem_links)} problems to scrape.")
        
        all_problems = []
        for problem_num, url in problem_links:
            problem_data = self.scrape_problem(url, problem_num)
            if problem_data:
                all_problems.append(problem_data)
            time.sleep(1)  # Be polite to the server
        
        # Save to JSON
        if self.contest_type == "AMC8":
            json_filename = f"amc8_{self.year}_problems.json"
        elif self.contest_type == "AMC10A":
            json_filename = f"amc10a_{self.year}_problems.json"
        elif self.contest_type == "AMC10B":
            json_filename = f"amc10b_{self.year}_problems.json"
        elif self.contest_type == "AMC12A":
            json_filename = f"amc12a_{self.year}_problems.json"
        elif self.contest_type == "AMC12B":
            json_filename = f"amc12b_{self.year}_problems.json"
        output_file = self.output_dir / json_filename
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_problems, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Scraping complete! Saved {len(all_problems)} problems to {output_file}")
        return all_problems

