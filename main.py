from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import re
import argparse


def parse_projects(html_content):
    """Parse the HTML content and extract project details"""
    soup = BeautifulSoup(html_content, 'html.parser')
    projects = []
    
    # Find all project cards
    project_cards = soup.find_all('div', class_=re.compile(r'bg-white.*border.*rounded-sm'))
    
    print(f"Found {len(project_cards)} project cards")
    
    for card in project_cards:
        try:
            project_data = {}
            
            # Extract Project Name
            project_name_elem = card.find('p', class_=re.compile(r'.*font-bold.*text-primary.*'))
            if project_name_elem:
                project_data['project_name'] = project_name_elem.text.strip()
            
            # Extract Builder Name
            builder_elem = card.find('a', href=re.compile(r'/builder/'))
            if builder_elem:
                builder_name = builder_elem.find('p')
                if builder_name:
                    project_data['builder_name'] = builder_name.text.strip()
            
            # Extract Possession Date
            possession_elem = card.find('span', class_='text-[#0E8744]')
            if possession_elem:
                possession_text = possession_elem.text.strip()
                project_data['possession_date'] = possession_text
            
            # Extract flat configurations (BHK, size, price)
            configurations = []
            config_divs = card.find_all('div', class_=re.compile(r'text-\[#234e70\].*list-fx-features'))
            
            for config_div in config_divs:
                config = {}
                items = config_div.find_all('div', class_='text-xs')
                
                if len(items) >= 3:
                    # BHK configuration
                    config['bhk'] = items[0].text.strip()
                    # Size
                    config['size'] = items[1].text.strip()
                    # Price
                    config['price'] = items[2].text.strip()
                    
                    configurations.append(config)
            
            project_data['configurations'] = configurations
            
            # Only add projects that have at least a name
            if 'project_name' in project_data:
                projects.append(project_data)
                
        except Exception as e:
            print(f"Error parsing a project card: {e}")
            continue
    
    return projects


def main(location, min_price, max_price, config):
    # Build the full URL with parameters
    base_url = "https://housiey.com/in/pune/"
    location = location.lower().replace(" ", "-")  # Ensure location is formatted correctly for URL
    min_price = min_price
    max_price = max_price
    config = config
    params = f"?isMapView=true&config={config}&min={min_price}&max={max_price}&downPayment=&availability_status=1"
    full_url = base_url + location + params
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")  # Handle SSL issues
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    try:
        print(f"Opening browser and navigating to {full_url}...")
        
        # Initialize the Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to the URL
        driver.get(full_url)
        
        # Wait for page to load (wait for body tag)
        print("Waiting for page to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(3)
        
        # Get the page source (DOM content)
        page_source = driver.page_source
        
        print(f"\n{'='*50}")
        print(f"Page Title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        print(f"{'='*50}\n")
        
        # Print the DOM content
        print("DOM Content (first 3000 characters):")
        print(page_source[:3000])
        
        # Save full DOM to file
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print(f"\n{'='*50}")
        print("Full DOM content saved to page_source.html")
        
        # Parse projects from the HTML
        print(f"\n{'='*50}")
        print("Parsing project details...")
        projects = parse_projects(page_source)
        
        # Display extracted projects
        print(f"\n{'='*50}")
        print(f"Extracted {len(projects)} projects:\n")
        
        # Save extracted data to JSON. Under configurations, if bhk value contains Sold Out, we will ignore that configuration and not include it in the JSON output. Also if after not considering such configurations if there are no configurations left for a project, we will ignore that project and not include it in the JSON output
        # Filter out "Sold Out" configurations and projects without valid configurations
        filtered_projects = []
        for project in projects:
            if 'configurations' in project:
                valid_configs = [config for config in project['configurations'] if 'Sold Out' not in config.get('bhk', '')]
                if valid_configs:  # Only include project if it has valid configurations
                    project['configurations'] = valid_configs
                    filtered_projects.append(project)
            # elif project:  # Include projects without configurations field
            #     filtered_projects.append(project)

        for i, project in enumerate(filtered_projects, 1):
            print(f"\nProject {i}:")
            print(f"  Name: {project.get('project_name', 'N/A')}")
            print(f"  Builder: {project.get('builder_name', 'N/A')}")
            print(f"  Possession: {project.get('possession_date', 'N/A')}")
            
            if project.get('configurations'):
                print(f"  Configurations:")
                for config in project['configurations']:
                    print(f"    - {config.get('bhk', 'N/A')}: {config.get('size', 'N/A')} @ {config.get('price', 'N/A')}")
            else:
                print(f"  Configurations: N/A")
        
        # Save extracted data to JSON
        with open(f"projects_data_{location}.json", "w", encoding="utf-8") as f:
            json.dump(filtered_projects, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*50}")
        print("Project data saved to projects_data.json")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            driver.quit()
            print("Browser closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape project details from housiey.com")
    parser.add_argument("--location", type=str, default="tathawade", help="Location to scrape projects for (default: tathawade)")
    parser.add_argument("--min_price", type=int, default=2500000, help="Minimum price filter (default: 0)")
    parser.add_argument("--max_price", type=int, default=9999999999, help="Maximum price filter (default: 9999999999)")
    parser.add_argument("--config", type=str, default="", help="Configuration filter (default: 156,147,113,72,46,33,14-152,115,93,47,22-151,150,145,94,71,37,17)") # 156,147,113,72,46,33,14-152,115,93,47,22-151,150,145,94,71,37,17

    args = parser.parse_args()
    
    main(args.location, args.min_price, args.max_price, args.config)