#!/usr/bin/env python3
"""
HTML renderer for AMC 8 problems.
Converts JSON data into HTML files that recreate the original problem pages.
Supports multiple years with year-based directory structure.
"""

import json
from pathlib import Path
from html import escape

class HTMLRenderer:
    def __init__(self, contest_type, year=None, base_data_dir="data"):
        """
        Initialize renderer for a specific contest type and year.
        
        Args:
            contest_type: One of "AMC8", "AMC10A", "AMC10B"
            year: Year as integer (e.g., 2025). If None, renders all years found.
            base_data_dir: Base directory for data (default: "data")
        """
        self.contest_type = contest_type
        self.year = year
        self.base_data_dir = Path(base_data_dir)
        
        # Determine directory structure based on contest type
        if contest_type == "AMC8":
            self.contest_name = "AMC 8"
            self.dir_name = "AMC8"
            self.json_prefix = "amc8"
        elif contest_type == "AMC10A":
            self.contest_name = "AMC 10A"
            self.dir_name = "AMC10A"
            self.json_prefix = "amc10a"
        elif contest_type == "AMC10B":
            self.contest_name = "AMC 10B"
            self.dir_name = "AMC10B"
            self.json_prefix = "amc10b"
        elif contest_type == "AMC12A":
            self.contest_name = "AMC 12A"
            self.dir_name = "AMC12A"
            self.json_prefix = "amc12a"
        elif contest_type == "AMC12B":
            self.contest_name = "AMC 12B"
            self.dir_name = "AMC12B"
            self.json_prefix = "amc12b"
        else:
            raise ValueError(f"Unknown contest type: {contest_type}")
        
        # Structure: data/CONTEST_TYPE/YEAR/
        if year:
            self.year_dir = self.base_data_dir / self.dir_name / str(year)
            self.output_dir = self.year_dir / "html"
            self.output_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.year_dir = None
            self.output_dir = None
    
    def render_content_item(self, item):
        """Render a single content item (text, image, or HTML)."""
        if item['type'] == 'text':
            return escape(item['content'])
        elif item['type'] == 'image':
            # Fix path: HTML files are in html/ subdirectory, images are in images/ subdirectory
            # So we need to go up one level: ../images/filename
            image_path = item["local_path"]
            if not image_path.startswith('../'):
                # Convert images/filename to ../images/filename
                image_path = '../' + image_path
            img_tag = f'<img src="{image_path}" alt="{escape(item.get("alt", ""))}"'
            if item.get('width'):
                img_tag += f' width="{item["width"]}"'
            if item.get('height'):
                img_tag += f' height="{item["height"]}"'
            img_tag += ' />'
            return img_tag
        elif item['type'] == 'line_break':
            return '<br />'
        elif item['type'] == 'html':
            # Use the preserved HTML if available, otherwise render as text
            return item.get('html', escape(item['content']))
        return ''
    
    def render_problem_only(self, problem_data):
        """Render only the problem statement (without solutions)."""
        html_parts = []
        
        # Problem header
        html_parts.append(f'<h2 id="Problem">Problem</h2>')
        html_parts.append('<div class="problem-content">')
        
        # Problem content
        for item in problem_data.get('content', []):
            html_parts.append(self.render_content_item(item))
        
        # Answer choices
        if problem_data.get('answer_choices'):
            html_parts.append('<div class="answer-choices">')
            for choice in problem_data['answer_choices']:
                html_parts.append(
                    f'<p><strong>({choice["letter"]})</strong> {escape(choice["text"])}</p>'
                )
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def render_solutions_only(self, problem_data):
        """Render only the solutions (without problem statement)."""
        html_parts = []
        
        if not problem_data.get('solutions'):
            html_parts.append('<p>No solutions available.</p>')
            return '\n'.join(html_parts)
        
        # Solutions
        for solution in problem_data.get('solutions', []):
            html_parts.append(f'<h2 id="Solution_{solution["number"]}">Solution {solution["number"]}</h2>')
            html_parts.append('<div class="solution-content">')
            
            for item in solution.get('content', []):
                html_parts.append(self.render_content_item(item))
            
            html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def get_common_styles(self):
        """Get common CSS styles for all pages."""
        return """        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h2 {
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 5px;
            margin-top: 30px;
        }
        .problem-content, .solution-content {
            margin: 20px 0;
            line-height: 1.8;
        }
        /* Ensure inline math images flow with text */
        .problem-content img[alt*="$"]:not([alt*="[asy]"]), 
        .solution-content img[alt*="$"]:not([alt*="[asy]"]) {
            display: inline-block;
            margin: 0 2px;
            vertical-align: middle;
        }
        .answer-choices {
            margin: 20px 0;
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .answer-choices p {
            margin: 10px 0;
        }
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        img[alt*="[asy]"] {
            /* Style for Asymptote diagrams */
            background-color: #fafafa;
        }
        p {
            margin: 10px 0;
        }
        .nav-links {
            margin: 20px 0;
            padding: 15px;
            background-color: #e3f2fd;
            border-radius: 5px;
        }
        .nav-links a {
            color: #2196F3;
            text-decoration: none;
            margin-right: 15px;
        }
        .nav-links a:hover {
            text-decoration: underline;
        }"""
    
    def render_problem_page(self, problem_data):
        """Render a complete HTML page with only the problem statement."""
        problem_html = self.render_problem_only(problem_data)
        year = problem_data.get('year', self.year or 'AMC')
        contest_name = problem_data.get('contest_name', self.contest_name)
        problem_num = problem_data['number']
        
        # Navigation links
        nav_html = f'<div class="nav-links"><a href="solution_{problem_num}.html">View Solutions</a></div>'
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{year} {contest_name} - Problem {problem_num}</title>
    <style>
{self.get_common_styles()}
    </style>
</head>
<body>
    <h1>{year} {contest_name} - Problem {problem_num}</h1>
    {nav_html}
    {problem_html}
</body>
</html>"""
    
    def render_solution_page(self, problem_data):
        """Render a complete HTML page with only the solutions."""
        solutions_html = self.render_solutions_only(problem_data)
        year = problem_data.get('year', self.year or 'AMC')
        contest_name = problem_data.get('contest_name', self.contest_name)
        problem_num = problem_data['number']
        
        # Navigation links
        nav_html = f'<div class="nav-links"><a href="problem_{problem_num}.html">View Problem</a></div>'
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{year} {contest_name} - Problem {problem_num} Solutions</title>
    <style>
{self.get_common_styles()}
    </style>
</head>
<body>
    <h1>{year} {contest_name} - Problem {problem_num} Solutions</h1>
    {nav_html}
    {solutions_html}
</body>
</html>"""
    
    def render_all(self):
        """Render all problems from JSON file, creating separate files for problems and solutions."""
        if not self.year_dir:
            print("Error: Year not specified. Please provide a year.")
            return
        
        json_file = self.year_dir / f"{self.json_prefix}_{self.year}_problems.json"
        
        if not json_file.exists():
            print(f"Error: {json_file} not found. Please run scraper.py first.")
            return
        
        with open(json_file, 'r', encoding='utf-8') as f:
            problems = json.load(f)
        
        # Delete existing HTML files first
        print(f"Cleaning up existing HTML files in {self.output_dir}...")
        for html_file in self.output_dir.glob("*.html"):
            if html_file.name != "index.html":  # Keep index.html for now
                html_file.unlink()
        
        # Render individual problem pages (problem only)
        for problem in problems:
            problem_html = self.render_problem_page(problem)
            problem_file = self.output_dir / f"problem_{problem['number']}.html"
            with open(problem_file, 'w', encoding='utf-8') as f:
                f.write(problem_html)
            print(f"Rendered Problem {problem['number']}")
        
        # Render individual solution pages (solutions only)
        for problem in problems:
            if problem.get('solutions'):
                solution_html = self.render_solution_page(problem)
                solution_file = self.output_dir / f"solution_{problem['number']}.html"
                with open(solution_file, 'w', encoding='utf-8') as f:
                    f.write(solution_html)
                print(f"Rendered Solution {problem['number']}")
        
        # Create index page
        self.create_index_page(problems)
        
        print(f"\n✓ Rendering complete! HTML files saved to {self.output_dir}")
    
    def create_index_page(self, problems):
        """Create an index page linking to all problems and solutions."""
        year = problems[0].get('year', self.year) if problems else self.year or 'AMC'
        contest_name = problems[0].get('contest_name', self.contest_name) if problems else self.contest_name
        links_html = '\n'.join([
            f'<li><a href="problem_{p["number"]}.html">Problem {p["number"]}</a> | <a href="solution_{p["number"]}.html">Solutions</a></li>'
            for p in problems
        ])
        
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{year} {contest_name} Problems</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        ul {{
            list-style-type: none;
            padding: 0;
        }}
        li {{
            margin: 10px 0;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }}
        li:hover {{
            background-color: #e0e0e0;
        }}
        a {{
            text-decoration: none;
            color: #2196F3;
            font-size: 18px;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <h1>{year} {contest_name} Problems</h1>
    <ul>
        {links_html}
    </ul>
</body>
</html>"""
        
        index_file = self.output_dir / "index.html"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_html)
        print(f"Created index page: {index_file}")

def render_all_years(contest_type, start_year=2024, end_year=1999, base_data_dir="data"):
    """Render HTML for all years in the specified range."""
    years = list(range(start_year, end_year - 1, -1))
    
    print(f"\n{'='*70}")
    print(f"Rendering HTML for {contest_type} Problems - Years {start_year} to {end_year}")
    print(f"{'='*70}\n")
    
    for year in years:
        try:
            renderer = HTMLRenderer(contest_type=contest_type, year=year, base_data_dir=base_data_dir)
            renderer.render_all()
        except Exception as e:
            print(f"\n✗ Error rendering {year}: {e}")
            continue

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        contest_type = sys.argv[1].upper()
        if contest_type not in ["AMC8", "AMC10A", "AMC10B", "AMC12A", "AMC12B"]:
            print("Error: Contest type must be one of: AMC8, AMC10A, AMC10B, AMC12A, AMC12B")
            sys.exit(1)
        
        if len(sys.argv) > 2:
            year = int(sys.argv[2])
            renderer = HTMLRenderer(contest_type=contest_type, year=year)
            renderer.render_all()
        else:
            # Default years based on contest type
            if contest_type == "AMC8":
                render_all_years(contest_type, 2024, 1999)
            else:  # AMC10A, AMC10B, AMC12A, or AMC12B
                render_all_years(contest_type, 2025, 2002)
    else:
        # Default: render all AMC8 years
        print("Usage: python renderer.py [AMC8|AMC10A|AMC10B|AMC12A|AMC12B] [year]")
        print("       If year is omitted, renders all available years")

