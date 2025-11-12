#!/usr/bin/env python3
"""
Main script to scrape AMC 8 problems for multiple years (2024-1999).
"""

from scraper import AMCScraper
import sys

def scrape_years(start_year=2024, end_year=1999):
    """
    Scrape AMC 8 problems for a range of years.
    
    Args:
        start_year: Starting year (default: 2024)
        end_year: Ending year (default: 1999)
    """
    years = list(range(start_year, end_year - 1, -1))  # Descending order
    
    print(f"\n{'='*70}")
    print(f"AMC 8 Problem Scraper - Years {start_year} to {end_year}")
    print(f"{'='*70}\n")
    
    results = {}
    
    for year in years:
        try:
            scraper = AMCScraper("AMC8", year)
            problems = scraper.scrape_all()
            results[year] = {
                'success': True,
                'count': len(problems) if problems else 0
            }
        except Exception as e:
            print(f"\n✗ Error scraping {year}: {e}")
            results[year] = {
                'success': False,
                'error': str(e)
            }
            continue
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for year in years:
        if results[year]['success']:
            print(f"✓ {year}: {results[year]['count']} problems scraped")
        else:
            print(f"✗ {year}: Failed - {results[year].get('error', 'Unknown error')}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Allow specifying a single year or range
        if len(sys.argv) == 2:
            year = int(sys.argv[1])
            scraper = AMCScraper("AMC8", year)
            scraper.scrape_all()
        elif len(sys.argv) == 3:
            start = int(sys.argv[1])
            end = int(sys.argv[2])
            scrape_years(start, end)
        else:
            print("Usage: python scrape_all_years.py [start_year] [end_year]")
            print("       python scrape_all_years.py [year]  (single year)")
    else:
        # Default: scrape 2024 to 1999
        scrape_years(2024, 1999)

