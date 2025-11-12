#!/usr/bin/env python3
"""
Script to scrape AMC 10 problems (both A and B variants) for multiple years.
"""

from scraper import AMCScraper
import sys

def scrape_amc10_years(start_year=2025, end_year=2002):
    """
    Scrape AMC 10A and AMC 10B problems for a range of years.
    
    Args:
        start_year: Starting year (default: 2025)
        end_year: Ending year (default: 2002)
    """
    years = list(range(start_year, end_year - 1, -1))  # Descending order
    
    print(f"\n{'='*70}")
    print(f"AMC 10 Problem Scraper - Years {start_year} to {end_year}")
    print(f"{'='*70}\n")
    
    results = {}
    
    for year in years:
        results[year] = {}
        
        # Scrape AMC 10A
        try:
            print(f"\n--- {year} AMC 10A ---")
            scraper_a = AMCScraper("AMC10A", year)
            problems_a = scraper_a.scrape_all()
            results[year]['AMC10A'] = {
                'success': True,
                'count': len(problems_a) if problems_a else 0
            }
        except Exception as e:
            print(f"\n✗ Error scraping {year} AMC 10A: {e}")
            results[year]['AMC10A'] = {
                'success': False,
                'error': str(e)
            }
        
        # Scrape AMC 10B
        try:
            print(f"\n--- {year} AMC 10B ---")
            scraper_b = AMCScraper("AMC10B", year)
            problems_b = scraper_b.scrape_all()
            results[year]['AMC10B'] = {
                'success': True,
                'count': len(problems_b) if problems_b else 0
            }
        except Exception as e:
            print(f"\n✗ Error scraping {year} AMC 10B: {e}")
            results[year]['AMC10B'] = {
                'success': False,
                'error': str(e)
            }
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for year in years:
        print(f"\n{year}:")
        if results[year]['AMC10A']['success']:
            print(f"  ✓ AMC 10A: {results[year]['AMC10A']['count']} problems scraped")
        else:
            print(f"  ✗ AMC 10A: Failed - {results[year]['AMC10A'].get('error', 'Unknown error')}")
        
        if results[year]['AMC10B']['success']:
            print(f"  ✓ AMC 10B: {results[year]['AMC10B']['count']} problems scraped")
        else:
            print(f"  ✗ AMC 10B: Failed - {results[year]['AMC10B'].get('error', 'Unknown error')}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Allow specifying a single year or range
        if len(sys.argv) == 2:
            year = int(sys.argv[1])
            print(f"Scraping {year} AMC 10A and 10B...")
            scraper_a = AMCScraper("AMC10A", year)
            scraper_a.scrape_all()
            scraper_b = AMCScraper("AMC10B", year)
            scraper_b.scrape_all()
        elif len(sys.argv) == 3:
            start = int(sys.argv[1])
            end = int(sys.argv[2])
            scrape_amc10_years(start, end)
        else:
            print("Usage: python scrape_amc10_years.py [start_year] [end_year]")
            print("       python scrape_amc10_years.py [year]  (single year)")
    else:
        # Default: scrape 2025 to 2002
        scrape_amc10_years(2025, 2002)

