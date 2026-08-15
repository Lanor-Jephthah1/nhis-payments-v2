import os
import time
import os
import re
import json
import argparse
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Configuration
URL = 'https://www.nhis.gov.gh/payments'
WAIT_TIMEOUT = 15
CSV_FILENAME = "nhis_payments_v2.csv"
CHECKPOINT_FILE = "nhis_checkpoint_v2.txt"
HEADERS = ["Facility Name", "District", "Amount Paid", "Claim Month", "Payment Date"]

def setup_driver(headless=False):
    """Initializes the Chrome WebDriver using webdriver-manager."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Automatically download and use the correct chromedriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver

def load_checkpoint():
    """Loads progress from previous run"""
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            return int(f.read().strip())
    except:
        return 1

def save_checkpoint(page_num):
    """Saves current progress"""
    with open(CHECKPOINT_FILE, 'w') as f:
        f.write(str(page_num))

def save_to_csv(data):
    """Appends data to the CSV file safely."""
    if not data:
        return
        
    df = pd.DataFrame(data, columns=HEADERS)
    df = df.dropna(how='all')
    df = df[df[HEADERS[0]].str.strip() != ""]
    
    if "District" in df.columns:
        df["District"] = df["District"].replace(['#REF!', '#REF!/'], 'Unknown')
    
    file_exists = os.path.exists(CSV_FILENAME)
    df.to_csv(CSV_FILENAME, mode='a', header=not file_exists, index=False)

@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(TimeoutException)
)
def wait_for_table(wait):
    """Waits for the master table to appear, with automatic retries on timeout."""
    return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table.rgMasterTable')))

def update_status(action, progress, detail=""):
    try:
        with open("scraper_status.json", "w") as f:
            json.dump({
                "action": action,
                "progress": progress,
                "detail": detail
            }, f)
    except:
        pass

def fast_forward(driver, wait, target_page):
    """Navigates to the target page before starting scraping."""
    console.print(f"[yellow]Fast-forwarding to page {target_page}...[/yellow]")
    
    # Try the instant JS jump first
    try:
        table = wait_for_table(wait)
        grid_el = driver.find_element(By.CSS_SELECTOR, ".RadGrid")
        grid_id = grid_el.get_attribute("id")
        
        console.print("[cyan]Attempting instant JavaScript jump...[/cyan]")
        driver.execute_script(f"""
            setTimeout(function() {{
                var grid = $find('{grid_id}');
                if (grid) {{
                    grid.get_masterTableView().set_currentPageIndex({target_page - 1});
                }}
            }}, 0);
        """)
        
        wait.until(EC.staleness_of(table))
        wait_for_table(wait)
        update_status("Fast-forwarding", f"Jumped directly to page {target_page}", "Used Telerik API to instantly skip intermediate pages")
        return target_page
        
    except Exception as e:
        console.print(f"[yellow]JS fast-forward failed, falling back to manual clicks...[/yellow]")
    
    current_page = 1
    while current_page < target_page:
        update_status("Fast-forwarding", f"Page {current_page} of {target_page}", "Silently skipping pages to reach checkpoint")
        try:
            table = wait_for_table(wait)
            next_btn = driver.find_element(By.CSS_SELECTOR, "button.rgPageNext[title='Next Page']")
            if "disabled" in next_btn.get_attribute("class"):
                console.print("[red]Target page is beyond the last available page![/red]")
                break
                
            driver.execute_script("arguments[0].scrollIntoView();", next_btn)
            driver.execute_script("arguments[0].click();", next_btn)
            wait.until(EC.staleness_of(table))
            current_page += 1
            time.sleep(0.5)
        except Exception as e:
            console.print(f"[red]Error during fast-forward: {e}[/red]")
            raise Exception("Fast-forward failed to reach target page. Aborting to prevent data corruption.")
            
    return current_page

def scrape_data(headless=False, force_restart=False):
    driver = setup_driver(headless)
    console.print(f"[bold green]Starting Scraper on {URL}[/bold green]")
    driver.get(URL)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    if force_restart and os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        if os.path.exists(CSV_FILENAME):
            os.remove(CSV_FILENAME)

    start_page = load_checkpoint()
    total_records = 0

    if start_page > 1:
        console.print(f"[cyan]Resuming from checkpoint: Page {start_page}[/cyan]")
        start_page = fast_forward(driver, wait, start_page)

    current_page = start_page

    try:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            transient=False,
        ) as progress:
            task = progress.add_task(f"Scraping page {current_page}...", total=None)

            while True:
                update_status("Scraping", f"Page {current_page}", "Extracting new records from website")
                table = wait_for_table(wait)
                rows = table.find_elements(By.CSS_SELECTOR, 'tr.rgRow, tr.rgAltRow')

                if not rows:
                    console.print("[yellow]No data found - stopping.[/yellow]")
                    break

                # Extract data from current page
                new_rows = []
                for row in rows:
                    cells = [cell.text.strip() for cell in row.find_elements(By.TAG_NAME, 'td')]
                    if len(cells) == len(HEADERS):
                        new_rows.append(cells)

                if new_rows:
                    save_to_csv(new_rows)
                    total_records += len(new_rows)
                    
                progress.update(task, description=f"Scraped page {current_page} | Added {len(new_rows)} rows | Total this session: {total_records}")
                save_checkpoint(current_page + 1)

                # Click Next button
                max_retries = 3
                success = False
                for attempt in range(max_retries):
                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, "button.rgPageNext[title='Next Page']")

                        if "disabled" in next_btn.get_attribute("class"):
                            console.print("\n[bold green]Reached last page. Scraping complete![/bold green]")
                            if os.path.exists(CHECKPOINT_FILE):
                                os.remove(CHECKPOINT_FILE)
                            success = True # not an error
                            break

                        # Use Javascript to click to avoid ElementClickInterceptedException from overlays
                        driver.execute_script("arguments[0].click();", next_btn)

                        # Wait for new page to load
                        wait.until(EC.staleness_of(table))
                        current_page += 1
                        time.sleep(0.5)
                        success = True
                        break # Success, break out of retry loop

                    except NoSuchElementException:
                        console.print("\n[yellow]Next button not found. Ending scrape.[/yellow]")
                        break # Break retry loop
                    except Exception as e:
                        if attempt == max_retries - 1:
                            error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
                            console.print(f"\n[red]Error clicking next button after {max_retries} attempts: {error_msg}[/red]")
                            break
                        console.print(f"\n[yellow]Retry {attempt + 1}/{max_retries} clicking next button...[/yellow]")
                        time.sleep(2)
                
                # If we exhausted retries and didn't succeed, we need to break the outer loop
                if not success:
                    break

    except Exception as e:
        error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
        console.print(f"\n[bold red]Fatal error:[/bold red] {error_msg}")
    finally:
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NHIS Payments Scraper")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--restart", action="store_true", help="Ignore checkpoint and start from page 1")
    args = parser.parse_args()

    scrape_data(headless=args.headless, force_restart=args.restart)