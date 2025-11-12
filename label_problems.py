#!/usr/bin/env python3
"""
Label AMC problems with categories using OpenRouter API.
Processes screenshots and stores primary and secondary category labels.
"""

import os
import json
import base64
import argparse
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try to load .env from the script's directory or current working directory
    try:
        script_dir = Path(__file__).parent.resolve()
    except NameError:
        # __file__ not available, use current working directory
        script_dir = Path.cwd()
    
    env_path = script_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
    else:
        # Fallback to current working directory
        load_dotenv(override=True)
except ImportError:
    # python-dotenv not installed, continue without it
    pass
except Exception as e:
    # Silently continue if there's any issue loading .env
    import sys
    print(f"Warning: Could not load .env file: {e}", file=sys.stderr)

# Default prompt for category labeling
CATEGORY_PROMPT = """American Mathematics Competition (AMC) have these primary categories:

Arithmetic: Basic operations and concepts.

Algebra: Solving equations and systems, functions, and other algebraic topics.

Counting: Combinatorics, which includes permutations and combinations.

Geometry: Euclidean and other forms of geometry, including areas, volumes, and properties of shapes.

Number Theory: Properties of integers, divisibility rules, and more advanced concepts.

Probability: Calculating the likelihood of events.

Please tag this question with its most appropriate category, and an optional secondary category that has related skills. Give your output as in the format of ["primary category", "second category"] and leave the second an empty string if you decide the question is simple and doesn't need a second tag."""


class OpenRouterClient:
    """Client for OpenRouter API."""
    
    def __init__(self, api_key: str, model: str = "google/gemini-2.5-pro", base_url: str = "https://openrouter.ai/api/v1", timeout: int = 180):
        """
        Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            model: Model identifier (default: "google/gemini-2.5-pro" which supports vision)
            base_url: OpenRouter API base URL
            timeout: Request timeout in seconds (default: 180 for 3 minutes)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        
        # Set up session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def encode_image(self, image_path: Path) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def get_categories(self, image_path: Path, max_retries: int = 3) -> Tuple[str, str]:
        """
        Get categories for an image using OpenRouter API.
        
        Args:
            image_path: Path to the screenshot image
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (primary_category, secondary_category)
        """
        # Encode image
        base64_image = self.encode_image(image_path)
        
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ylong/amcdatabase",  # Optional: for OpenRouter tracking
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": CATEGORY_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent categorization
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Parse the response - expect JSON array format
                try:
                    # Try to extract JSON array from response
                    json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                    if json_match:
                        categories = json.loads(json_match.group())
                    else:
                        categories = json.loads(content)
                    
                    primary = categories[0] if len(categories) > 0 else "Uncategorized"
                    secondary = categories[1] if len(categories) > 1 and categories[1] else ""
                    
                    return primary, secondary
                except (json.JSONDecodeError, IndexError) as e:
                    print(f"Warning: Failed to parse response for {image_path}: {content}")
                    print(f"Error: {e}")
                    # Try to extract categories from text response
                    if "Arithmetic" in content or "arithmetic" in content.lower():
                        return "Arithmetic", ""
                    elif "Algebra" in content or "algebra" in content.lower():
                        return "Algebra", ""
                    elif "Counting" in content or "counting" in content.lower():
                        return "Counting", ""
                    elif "Geometry" in content or "geometry" in content.lower():
                        return "Geometry", ""
                    elif "Number Theory" in content or "number theory" in content.lower():
                        return "Number Theory", ""
                    elif "Probability" in content or "probability" in content.lower():
                        return "Probability", ""
                    return "Uncategorized", ""
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Error calling API (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Failed to get categories for {image_path} after {max_retries} attempts: {e}")
                    return "Error", ""
        
        return "Error", ""


class ProblemLabeler:
    """Label AMC problems with categories."""
    
    def __init__(self, data_dir: Path, api_key: str, model: str = "google/gemini-2.5-pro", timeout: int = 180):
        """
        Initialize problem labeler.
        
        Args:
            data_dir: Base directory containing problem data
            api_key: OpenRouter API key
            model: Model identifier for OpenRouter
            timeout: Request timeout in seconds (default: 180 for 3 minutes)
        """
        self.data_dir = Path(data_dir)
        self.client = OpenRouterClient(api_key, model, timeout=timeout)
        self.labels_file = self.data_dir / "problem_labels.json"
        
        # Load existing labels
        self.labels = self.load_labels()
    
    def load_labels(self) -> Dict[str, Dict[str, str]]:
        """Load existing labels from JSON file."""
        if self.labels_file.exists():
            try:
                with open(self.labels_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {self.labels_file}, starting fresh.")
                return {}
        return {}
    
    def save_labels(self):
        """Save labels to JSON file."""
        self.labels_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.labels_file, 'w') as f:
            json.dump(self.labels, f, indent=2)
    
    def get_problem_key(self, test_type: str, year: str, problem_num: str) -> str:
        """Generate a unique key for a problem."""
        return f"{test_type}/{year}/problem_{problem_num}"
    
    def discover_screenshots(self, test_type: Optional[str] = None, 
                           year: Optional[str] = None) -> List[Tuple[Path, str, str, str]]:
        """
        Discover all screenshot files.
        
        Returns:
            List of tuples: (screenshot_path, test_type, year, problem_number)
        """
        screenshots = []
        
        # Pattern: data/test-type/year/screenshot/problem_x.png
        for test_dir in self.data_dir.iterdir():
            if not test_dir.is_dir():
                continue
            
            test_type_name = test_dir.name
            if test_type and test_type_name != test_type:
                continue
            
            for year_dir in test_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                
                year_str = year_dir.name
                if year and year_str != year:
                    continue
                
                screenshot_dir = year_dir / "screenshot"
                if not screenshot_dir.exists():
                    continue
                
                for screenshot_file in screenshot_dir.glob("problem_*.png"):
                    problem_num = screenshot_file.stem.replace("problem_", "")
                    screenshots.append((screenshot_file, test_type_name, year_str, problem_num))
        
        return sorted(screenshots)
    
    def process_problems(self, test_type: Optional[str] = None, 
                        year: Optional[str] = None,
                        limit: Optional[int] = None,
                        delay: float = 1.0):
        """
        Process problems and label them.
        
        Args:
            test_type: Filter by test type (e.g., "AMC10A")
            year: Filter by year (e.g., "2024")
            limit: Maximum number of problems to process (None for all)
            delay: Delay between API calls in seconds
        """
        screenshots = self.discover_screenshots(test_type, year)
        
        if limit:
            screenshots = screenshots[:limit]
        
        total = len(screenshots)
        processed = 0
        skipped = 0
        
        print(f"Found {total} problems to process.")
        print(f"Request timeout: {self.client.timeout} seconds ({self.client.timeout / 60:.1f} minutes)")
        print(f"Delay between calls: {delay} seconds")
        print()
        
        for screenshot_path, test_type_name, year_str, problem_num in screenshots:
            problem_key = self.get_problem_key(test_type_name, year_str, problem_num)
            
            # Skip if already labeled
            if problem_key in self.labels:
                skipped += 1
                print(f"[{processed + skipped}/{total}] Skipping {problem_key} (already labeled)")
                continue
            
            print(f"[{processed + skipped + 1}/{total}] Processing {problem_key}...")
            
            primary, secondary = self.client.get_categories(screenshot_path)
            
            self.labels[problem_key] = {
                "test_type": test_type_name,
                "year": year_str,
                "problem_number": problem_num,
                "primary_category": primary,
                "secondary_category": secondary,
                "screenshot_path": str(screenshot_path.relative_to(self.data_dir))
            }
            
            # Save after each problem to avoid data loss
            self.save_labels()
            
            processed += 1
            print(f"  → Primary: {primary}, Secondary: {secondary}")
            
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
        
        print(f"\nCompleted: {processed} processed, {skipped} skipped")
        print(f"Labels saved to {self.labels_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Label AMC problems with categories using OpenRouter API"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Base directory containing problem data (default: data)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenRouter API key (or set OPENROUTER_API_KEY environment variable)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="google/gemini-2.5-pro",
        help="OpenRouter model identifier (default: google/gemini-2.5-pro)"
    )
    parser.add_argument(
        "--test-type",
        type=str,
        help="Filter by test type (e.g., AMC10A, AMC12B)"
    )
    parser.add_argument(
        "--year",
        type=str,
        help="Filter by year (e.g., 2024)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of problems to process"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between API calls in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Request timeout in seconds (default: 180 for 3 minutes, or from OPENROUTER_TIMEOUT env var)"
    )
    
    args = parser.parse_args()
    
    # Get API key (from .env, environment variable, or command line)
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        # Debug: Check if .env was loaded
        import sys
        script_dir_debug = Path(__file__).parent.resolve() if '__file__' in globals() else Path.cwd()
        env_path_debug = script_dir_debug / ".env"
        print("Error: OpenRouter API key required.")
        print(f"Debug: Looking for .env at {env_path_debug}")
        print(f"Debug: .env exists: {env_path_debug.exists()}")
        print(f"Debug: Current working directory: {Path.cwd()}")
        print("Options:")
        print("  1. Create a .env file with OPENROUTER_API_KEY=your-key")
        print("  2. Set OPENROUTER_API_KEY environment variable")
        print("  3. Use --api-key command line argument")
        return 1
    
    # Get model (from .env, environment variable, command line, or default)
    model = args.model or os.getenv("OPENROUTER_MODEL") or "google/gemini-2.5-pro"
    
    # Get timeout (from .env, environment variable, command line, or default)
    timeout = args.timeout
    if timeout is None:
        timeout_str = os.getenv("OPENROUTER_TIMEOUT")
        timeout = int(timeout_str) if timeout_str else 180
    
    # Initialize labeler
    labeler = ProblemLabeler(
        data_dir=Path(args.data_dir),
        api_key=api_key,
        model=model,
        timeout=timeout
    )
    
    # Process problems
    try:
        labeler.process_problems(
            test_type=args.test_type,
            year=args.year,
            limit=args.limit,
            delay=args.delay
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving progress...")
        labeler.save_labels()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

