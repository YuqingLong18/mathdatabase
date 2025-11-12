# AMC 8 Problem Scraper

This project scrapes AMC 8 problems from multiple years (1999-2025) from the Art of Problem Solving wiki, preserving the exact structure including text, images, and solutions for local HTML recreation.

## Features

- Scrapes all 25 problems from AoPS wiki for multiple years
- Extracts up to 3 solutions per problem
- Downloads and saves all images locally
- Preserves the exact order and structure of content (text + images)
- Generates HTML files that recreate the original problem pages
- Creates index pages for easy navigation
- Organizes data by year in a structured directory format

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Scrape All Years (2024-1999)

To scrape all years from 2024 down to 1999:

```bash
python scrape_all_years.py
```

### Scrape a Single Year

To scrape a specific year:

```bash
python scrape_all_years.py 2024
```

Or use the scraper directly:

```bash
python -c "from scraper import AMC8Scraper; AMC8Scraper(2024).scrape_all()"
```

### Generate HTML Files

After scraping, generate HTML files for all years:

```bash
python renderer.py
```

Or for a specific year:

```bash
python renderer.py 2024
```

This will:
- Read the JSON data file for each year
- Generate individual HTML files for each problem in `data/AMC8/YEAR/html/`
- Create an index page (`data/AMC8/YEAR/html/index.html`) linking to all problems for that year

### Capture Screenshots of Problems

You can convert the rendered HTML problems into PNG screenshots that include the
prompt and the five answer choices. First install the browser automation
dependency (only needed once):

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

Then run the screenshot helper. The example below captures every problem for the
2024 AMC 10A and saves the files in `data/AMC10A/2024/screenshot/`:

```bash
python screenshot_problems.py --test-type AMC10A --year 2024
```

Use `--problem` to limit the run to specific numbers (pass the flag multiple
times), `--overwrite` to recreate existing PNGs, or `--show-browser` to debug in
headed mode. The script works for any test type/year that already has rendered
`problem_<n>.html` files under `data/<TEST>/<YEAR>/html/`. If your machine locks
down the default browser profile path, you can add
`--browser-channel chrome --browser-home data/.playwright-home` (or another
directory) so that all Playwright state lives inside the repo.

### Batch Screenshots for Every Contest

To iterate that same capture process across every contest (AMC8/10/12 A/B) and
every year that has rendered HTML, run:

```bash
python batch_screenshot_problems.py --browser-channel chrome --browser-home data/.playwright-home
```

Add `--dry-run` to preview the commands, `--test-type AMC10A --year 2024` to
limit the scope, or pass extra flags to each invocation by appending them after
`--`, for example `... -- --overwrite`.

### Label Problems with Categories

Use OpenRouter API to automatically categorize problems by sending screenshots
to a vision-capable LLM. The script processes screenshots and stores primary and
secondary category labels.

First, set up your configuration:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenRouter API key:
   ```bash
   OPENROUTER_API_KEY=your-api-key-here
   OPENROUTER_MODEL=openai/gpt-4o
   OPENROUTER_TIMEOUT=180
   ```

   - Get an API key at https://openrouter.ai/keys
   - `OPENROUTER_MODEL`: Model identifier (e.g., `openai/gpt-4o`, `google/gemini-2.0-flash-exp`)
   - `OPENROUTER_TIMEOUT`: Request timeout in seconds (default: 180 for 3 minutes). Slower models like Gemini 2.5 Pro may need the full 3 minutes.

Alternatively, you can set the environment variable directly:
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

Then run the labeling script:

```bash
# Label all problems (will skip already labeled ones)
python label_problems.py

# Label specific test type and year
python label_problems.py --test-type AMC10A --year 2024

# Test with a limited number of problems
python label_problems.py --test-type AMC10A --year 2024 --limit 5

# Adjust delay between API calls (default: 1.0 seconds)
python label_problems.py --delay 2.0

# Adjust request timeout (default: 180 seconds / 3 minutes)
# Useful for slower models like Gemini 2.5 Pro
python label_problems.py --timeout 180
```

The script will:
- Discover all screenshots in `data/<test-type>/<year>/screenshot/problem_*.png`
- Send each screenshot to OpenRouter API with a categorization prompt
- Store labels in `data/problem_labels.json` with the format:
  ```json
  {
    "AMC10A/2024/problem_1": {
      "test_type": "AMC10A",
      "year": "2024",
      "problem_number": "1",
      "primary_category": "Algebra",
      "secondary_category": "Arithmetic",
      "screenshot_path": "AMC10A/2024/screenshot/problem_1.png"
    }
  }
  ```
- Skip already labeled problems (resumable)
- Save progress after each problem to avoid data loss

Categories include: Arithmetic, Algebra, Counting, Geometry, Number Theory, and Probability.

## Project Structure

```
amcdatabase/
├── scraper.py              # Scraper class (year-aware)
├── scrape_all_years.py     # Main script to scrape multiple years
├── renderer.py             # HTML renderer (year-aware)
├── migrate_data.py         # Script to migrate old data structure
├── requirements.txt        # Python dependencies
├── data/
│   └── AMC8/
│       ├── 2025/
│       │   ├── amc8_2025_problems.json
│       │   ├── images/          # Downloaded images
│       │   └── html/             # Generated HTML files
│       │       ├── index.html
│       │       ├── problem_1.html
│       │       └── ...
│       ├── 2024/
│       │   ├── amc8_2024_problems.json
│       │   ├── images/
│       │   └── html/
│       ├── 2023/
│       └── ... (down to 1999)
```

## Data Format

The JSON file for each year contains an array of problems, each with:

```json
{
  "number": 1,
  "year": 2025,
  "content": [
    {"type": "text", "content": "..."},
    {"type": "image", "src": "...", "local_path": "...", "alt": "..."},
    ...
  ],
  "answer_choices": [
    {"letter": "A", "text": "..."},
    ...
  ],
  "solutions": [
    {
      "number": 1,
      "content": [...]
    },
    ...
  ]
}
```

## Examples

### Scrape 2024 AMC 8 only:
```bash
python scrape_all_years.py 2024
python renderer.py 2024
```

### Scrape range of years:
```bash
python scrape_all_years.py 2024 2020  # Scrapes 2024, 2023, 2022, 2021, 2020
```

### Render HTML for specific year:
```bash
python renderer.py 2024
```

## Notes

- The scraper includes delays between requests to be respectful to the server
- Images are downloaded and stored locally with descriptive filenames
- The HTML renderer preserves the original structure and formatting
- All content preserves the exact order of text and images as on the original pages
- Each year's data is stored in its own directory for easy organization
- Image paths in HTML are relative and work correctly with the directory structure

## Migration

If you have existing data in the old structure (`data/amc8_2025_problems.json`), run:

```bash
python migrate_data.py
```

This will move your existing 2025 data to the new structure (`data/AMC8/2025/`).

## License

Problems are copyrighted © by the Mathematical Association of America.
