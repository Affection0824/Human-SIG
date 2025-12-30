import argparse
import sys
from pathlib import Path
import importlib

# Add src to path if not already
sys.path.append(str(Path(__file__).parent))

SCRAPERS = {
    'selenium': 'src.scrapers.selenium_scraper',
    'lmarena': 'src.scrapers.lmarena_scraper',
    'frontiermath': 'src.scrapers.frontiermath_scraper',
    'artificial_analysis': 'src.scrapers.artificial_analysis_scraper',
    'vals_ai': 'src.scrapers.vals_ai_scraper',
    'pandas_read_html': 'src.scrapers.pandas_read_html_scraper',
}

def get_data_dir(method):
    # Assuming standard structure: data/raw/{method}
    return Path('data/raw') / method

def run_scraper(method):
    if method not in SCRAPERS:
        print(f"Error: Unknown method '{method}'")
        return

    module_name = SCRAPERS[method]
    try:
        module = importlib.import_module(module_name)
        data_dir = get_data_dir(method)
        print(f"=== Starting {method} scraper ===")
        module.run(data_dir)
        print(f"=== Finished {method} scraper ===\n")
    except Exception as e:
        print(f"Error running scraper for {method}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Human-SIG Experiment Runner")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Run data acquisition')
    scrape_parser.add_argument('--method', '-m', type=str, choices=list(SCRAPERS.keys()) + ['all'], default='all', help='Scraping method to run')

    # Add other commands here as needed (e.g., process, analyze)
    
    args = parser.parse_args()

    if args.command == 'scrape':
        if args.method == 'all':
            for method in SCRAPERS:
                run_scraper(method)
        else:
            run_scraper(args.method)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
