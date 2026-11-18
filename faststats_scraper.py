# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import Select, WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import os, time


# def download_faststats_reports(regions, url, download_dir):
#     os.makedirs(download_dir, exist_ok=True)

#     # Chrome options
#     options = webdriver.ChromeOptions()
#     prefs = {
#         "download.default_directory": download_dir,
#         "download.prompt_for_download": False,
#         "plugins.always_open_pdf_externally": True
#     }
#     options.add_experimental_option("prefs", prefs)
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--headless=new")

#     # Start browser
#     service = Service("/usr/local/bin/chromedriver")
#     driver = webdriver.Chrome(service=service, options=options)
#     wait = WebDriverWait(driver, 20)

#     print(f"\nNavigating to the reports page ...")
#     driver.get(url)

#     for region in regions:
#         print(f"\nProcessing: {region}")

#         # Step 1: Select region from dropdown
#         dropdown = wait.until(EC.presence_of_element_located((By.ID, "lmuArea")))
#         select = Select(dropdown)
#         select.select_by_visible_text(region)
#         time.sleep(2)

#         # Step 2: Find and click the View Report button
#         view_btn = driver.find_element(By.CSS_SELECTOR, "div[rel='lmu'] button")
#         driver.execute_script("arguments[0].click();", view_btn)
#         print("Clicked View Report button...")

#         time.sleep(2)

#     driver.quit()
#     print("All done!")

"""
Example:
    python faststats_scraper.py "Georgia submarkets"
    python faststats_scraper.py "Illinois counties" --regions "Cook County" "Lake County"
    # need to watch the browser?
    python faststats_scraper.py "Georgia submarkets" --headful
"""
import argparse, os, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from faststats_markets_config import faststats_sources


def download_faststats_reports(regions, url, download_dir, headless=True):
    os.makedirs(download_dir, exist_ok=True)

    chrome_opts = webdriver.ChromeOptions()
    chrome_opts.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
    })
    if headless:
        chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"),
                              options=chrome_opts)
    wait = WebDriverWait(driver, 20)

    print("\nOpening:", url)
    driver.get(url)

    for region in regions:
        print("   •", region)
        Select(wait.until(EC.presence_of_element_located((By.ID, "lmuArea")))
               ).select_by_visible_text(region)
        view_btn = driver.find_element(By.CSS_SELECTOR, "div[rel='lmu'] button")
        driver.execute_script("arguments[0].click();", view_btn)
        time.sleep(2)

    driver.quit()
    print("Finished")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download ShowingTime FastStats PDF reports."
        )
    parser.add_argument("market",
                        choices=faststats_sources.keys(),
                        help="Market key defined in faststats_config.py")
    parser.add_argument("--regions", nargs="+",
                        help="Override default region list for this run")
    parser.add_argument("--headful", action="store_true",
                        help="Run Chrome with a window instead of headless")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cfg = faststats_sources[args.market]

    download_faststats_reports(
        regions=args.regions or cfg["regions"],
        url=cfg["url"],
        download_dir=cfg["download_dir"],
        headless=not args.headful,
    )
