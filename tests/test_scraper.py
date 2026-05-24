import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from orchestrator import scrape_job_description

def test():
    url = "https://example.com"
    print(f"Testing scrape_job_description with URL: {url}")
    try:
        content = scrape_job_description(url)
        print("--- Scraped Content Start ---")
        print(content)
        print("--- Scraped Content End ---")
        if "Example Domain" in content:
            print("TEST PASSED: Scraped content successfully.")
        else:
            print("TEST FAILED: 'Example Domain' not found in scraped content.")
    except Exception as e:
        print(f"TEST FAILED with exception: {e}")

if __name__ == "__main__":
    test()
