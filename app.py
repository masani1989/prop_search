import streamlit as st
import json
import os
from datetime import datetime
import re
import subprocess
import sys

st.set_page_config(
    page_title="Housiey Property Search",
    page_icon="🏠",
    layout="wide"
)

# Initialize session state for storing scraped data
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = {}

def load_project_data(location):
    """Load project data from session state cache or JSON file"""
    # First check session state (in-memory cache)
    if location in st.session_state.scraped_data:
        return st.session_state.scraped_data[location]
    
    # Fallback to JSON file if it exists (for local development)
    filename = f"projects_data_{location}.json"
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Cache it in session state
            st.session_state.scraped_data[location] = data
            return data
    
    return []

def parse_price(price_str):
    """Convert price string to numeric value for comparison"""
    if not price_str:
        return 0
    
    # Extract numbers and units (L for Lakhs, Cr for Crores)
    match = re.search(r'([\d.]+)\s*([LC])', price_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        
        if unit == 'L':
            return value * 100000  # Lakhs to actual value
        elif unit == 'C':
            return value * 10000000  # Crores to actual value
    
    return 0

def parse_possession_date(possession_str):
    """Parse possession date string to datetime for comparison"""
    if not possession_str or possession_str == "N/A":
        return None
    
    # Try to extract month and year
    try:
        # Handle formats like "Dec, 2025" or "Ready to Move"
        if "Ready to Move" in possession_str or "Ready To Move" in possession_str:
            return datetime.now()
        
        # Extract month and year
        match = re.search(r'([A-Za-z]+)[,\s]+(\d{4})', possession_str)
        if match:
            month_str = match.group(1)
            year = int(match.group(2))
            
            # Convert month name to number
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
                'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
            }
            
            month = month_map.get(month_str, 1)
            return datetime(year, month, 1)
    except:
        pass
    
    return None

def extract_bhk_types(projects):
    """Extract unique BHK types from all projects"""
    bhk_types = set()
    for project in projects:
        for config in project.get('configurations', []):
            bhk = config.get('bhk', '')
            if bhk:
                bhk_types.add(bhk)
    return sorted(list(bhk_types))

def filter_projects(projects, search_query, price_range, bhk_filter, possession_range):
    """Filter projects based on search query, price range, BHK, and possession date"""
    filtered = []
    
    for project in projects:
        # Search filter
        if search_query:
            project_name = project.get('project_name', '').lower()
            builder_name = project.get('builder_name', '').lower()
            if search_query.lower() not in project_name and search_query.lower() not in builder_name:
                continue
        
        # Possession date filter
        possession_date = parse_possession_date(project.get('possession_date', ''))
        if possession_date:
            if not (possession_range[0] <= possession_date <= possession_range[1]):
                continue
        
        # Filter configurations based on price and BHK
        valid_configs = []
        for config in project.get('configurations', []):
            price = parse_price(config.get('price', ''))
            bhk = config.get('bhk', '')
            
            # Price filter
            if price < price_range[0] or price > price_range[1]:
                continue
            
            # BHK filter
            if bhk_filter and bhk not in bhk_filter:
                continue
            
            valid_configs.append(config)
        
        # Only include project if it has valid configurations
        if valid_configs:
            project_copy = project.copy()
            project_copy['configurations'] = valid_configs
            filtered.append(project_copy)
    
    return filtered

def run_scraper(location, min_price=2500000, max_price=9999999999, config=""):
    """Run the main.py scraper with specified parameters and store in memory"""
    try:
        # Run main.py with the location parameter
        result = subprocess.run(
            [sys.executable, "main.py", "--location", location, 
             "--min_price", str(min_price), "--max_price", str(max_price),
             "--config", config],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes timeout
        )
        
        if result.returncode == 0:
            # Load the scraped data and store in session state
            filename = f"projects_data_{location}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    st.session_state.scraped_data[location] = data
        
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Scraping timed out after 2 minutes"
    except Exception as e:
        return False, "", str(e)

# Main app
st.title("🏠 Housiey Property Search")
# st.markdown("Find your dream property in Pune")

# Sidebar filters
st.sidebar.header("Filters")

# Get available locations from session state cache and JSON files
available_locations = list(st.session_state.scraped_data.keys())

# Also check for JSON files (local development)
for file in os.listdir('.'):
    if file.startswith('projects_data_') and file.endswith('.json'):
        location = file.replace('projects_data_', '').replace('.json', '')
        if location not in available_locations:
            available_locations.append(location)

# Add common locations if not present
common_locations = ['wakad', 'tathawade', 'hinjewadi', 'baner', 'pimple-saudagar', 'balewadi', 'punawale', 'chinchwad', 'moshi', 'ravet', 'kharadi', 'akurdi', 'bavdhan']
for loc in common_locations:
    if loc not in available_locations:
        available_locations.append(loc)

# Location selector
location = st.sidebar.selectbox(
    "Select Location",
    options=available_locations,
    format_func=lambda x: x.capitalize().replace('-', ' ')
)

# Scraper Configuration Section
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Update Data")

# with st.sidebar.expander("Scraper Settings", expanded=False):
#     scraper_min_price = st.number_input(
#         "Min Price (₹)",
#         min_value=0,
#         max_value=100000000,
#         value=2500000,
#         step=100000,
#         help="Minimum price filter for scraping"
#     )
    
#     scraper_max_price = st.number_input(
#         "Max Price (₹)",
#         min_value=0,
#         max_value=999999999,
#         value=999999999,
#         step=100000,
#         help="Maximum price filter for scraping"
#     )
    
#     scraper_config = st.text_input(
#         "Config Filter",
#         value="",
#         help="Leave empty for all configurations or specify config IDs"
#     )

# Run scraper button
if st.sidebar.button("🔄 Scrape Data for " + location.capitalize().replace('-', ' '), type="primary"):
    with st.spinner(f"Scraping property data for {location.capitalize()}... This may take 1-2 minutes."):
        success, stdout, stderr = run_scraper(location) #, scraper_min_price, scraper_max_price, scraper_config)
        
        if success:
            st.sidebar.success(f"✅ Successfully scraped data for {location.capitalize()}!")
            # Force reload
            st.rerun()
        else:
            st.sidebar.error(f"❌ Failed to scrape data: {stderr}")
            if stdout:
                with st.sidebar.expander("View output"):
                    st.code(stdout)

st.sidebar.markdown("---")

# Load data
projects = load_project_data(location)

if not projects:
    st.warning(f"⚠️ No projects found for {location.capitalize().replace('-', ' ')}")
    st.info("💡 Click the 'Scrape Data' button in the sidebar to fetch fresh data for this location.")
    
    # Show cached locations if any exist
    if st.session_state.scraped_data:
        cached_locs = ", ".join([loc.capitalize() for loc in st.session_state.scraped_data.keys()])
        st.info(f"📦 Data available in cache for: {cached_locs}")
    else:
        st.info("📦 No data in cache. Data will be cleared when the app restarts.")
    
    st.stop()

# Search box
search_query = st.sidebar.text_input("🔍 Search Project or Builder", "")

# Price range slider
st.sidebar.subheader("Price Range")
min_price = 0
max_price = 50000000  # 5 Crores

price_range = st.sidebar.slider(
    "Select Price Range (₹)",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price),
    step=500000,
    format="₹%.1fL" if max_price <= 10000000 else "₹%.1fCr"
)

# Convert display format
price_display = (
    f"₹{price_range[0]/100000:.1f}L - ₹{price_range[1]/10000000:.1f}Cr"
)
st.sidebar.write(f"Selected: {price_display}")

# BHK Configuration filter
st.sidebar.subheader("BHK Configuration")
bhk_types = extract_bhk_types(projects)
bhk_filter = st.sidebar.multiselect(
    "Select BHK Types",
    options=bhk_types,
    default=bhk_types[3:5] if len(bhk_types) > 2 else bhk_types  # Default to 1BHK and 2BHK if available
)

# Possession date filter
st.sidebar.subheader("Possession Timeline")
current_year = datetime.now().year
possession_year_range = st.sidebar.slider(
    "Possession Year",
    min_value=current_year,
    max_value=current_year + 10,
    value=(current_year, current_year + 5)
)

possession_range = (
    datetime(possession_year_range[0], 1, 1),
    datetime(possession_year_range[1], 12, 31)
)

# Filter projects
filtered_projects = filter_projects(
    projects, 
    search_query, 
    price_range, 
    bhk_filter, 
    possession_range
)

# Display results
st.header(f"Properties in {location.capitalize()}")
st.write(f"Found **{len(filtered_projects)}** properties matching your criteria")

# Display projects
for i, project in enumerate(filtered_projects):
    with st.expander(f"**{project.get('project_name', 'N/A')}** by {project.get('builder_name', 'N/A')}", expanded=i < 3):
        col1, col2 = st.columns([1, 2])
        proj_name_link = f"https://housiey.com/projects/{project.get('project_name', '').lower().replace(' ', '-').replace('.', '')}"
        
        with col1:
            st.markdown("### Project Details")
            st.write(f"**Builder:** {project.get('builder_name', 'N/A')}")
            st.write(f"**Possession:** {project.get('possession_date', 'N/A')}")
            st.write(f"**Project Link:** {proj_name_link}")
        
        with col2:
            st.markdown("### Available Configurations")
            
            # Create a table for configurations
            if project.get('configurations'):
                config_data = []
                for config in project['configurations']:
                    config_data.append({
                        'BHK': config.get('bhk', 'N/A'),
                        'Size': config.get('size', 'N/A'),
                        'Price': config.get('price', 'N/A')
                    })
                
                # st.table(config_data)
                st.dataframe(config_data, hide_index=True)
            else:
                st.write("No configurations available")
        
        st.markdown("---")

# Summary statistics
if filtered_projects:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Summary")
    st.sidebar.metric("Total Projects", len(filtered_projects))
    
    # Count total configurations
    total_configs = sum(len(p.get('configurations', [])) for p in filtered_projects)
    st.sidebar.metric("Total Configurations", total_configs)
