# 🏠 Property Search

A Streamlit web application for searching and filtering real estate properties in Pune, India. The app scrapes property data from Housiey.com and provides an intuitive interface for property discovery.

## Features

- 🔍 **Smart Search**: Search by project or builder name
- 📍 **Multiple Locations**: Support for Wakad, Tathawade, Hinjewadi, Baner, and more
- 💰 **Price Filtering**: Slider-based price range filtering (₹25L - ₹5Cr)
- 🏡 **BHK Configuration**: Filter by 1BHK, 2BHK, 3BHK, etc.
- 📅 **Possession Timeline**: Filter by possession year
- 🔄 **Real-time Scraping**: Scrape fresh data directly from the app
- 💾 **In-Memory Caching**: Fast access with session-based caching

## Local Development

### Prerequisites
- Python 3.8+
- Chrome browser (for Selenium)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the scraper
python main.py --location wakad

# Run the Streamlit app
streamlit run app.py
```

## Deployment on Streamlit Cloud

### Important Notes

This app uses **in-memory caching** for Streamlit Cloud compatibility:
- Data is stored in `st.session_state` during the session
- **Data is lost when the app restarts** or when the session ends
- Users must scrape data fresh for each location they want to explore
- No persistent storage required (cloud-friendly)

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Files Required**
   - `app.py` - Main Streamlit application
   - `main.py` - Web scraper script
   - `requirements.txt` - Python dependencies
   - `packages.txt` - System packages (chromium for Selenium)
   - `.streamlit/config.toml` - Streamlit configuration

### How It Works on Cloud

1. User selects a location (e.g., Wakad)
2. If no data exists, user clicks "Scrape Data"
3. App runs the scraper and stores results in `st.session_state`
4. Data persists for the duration of the user's session
5. Filters and searches work on cached data
6. On app restart, cache is cleared and users re-scrape

### Limitations

- ⚠️ **Session-based**: Data cleared on app restart
- ⏱️ **Scraping time**: 1-2 minutes per location
- 🔄 **No persistence**: Users must re-scrape after session timeout
- 🌐 **Single user**: Each user maintains their own cache

## Alternative Storage Options

If you need persistent storage, consider:
- **AWS S3 / GCS**: Store JSON files in cloud storage
- **PostgreSQL**: Database for structured storage
- **GitHub API**: Commit scraped data back to repository

## Tech Stack

- **Frontend**: Streamlit
- **Web Scraping**: Selenium + BeautifulSoup
- **Data Processing**: Pandas
- **Browser Automation**: Chrome/Chromium

## Configuration

### Scraper Settings
Modify in `main.py`:
- `min_price`: Minimum property price (default: ₹25L)
- `max_price`: Maximum property price (default: ₹10Cr)
- `config`: BHK configuration filter

### App Settings
Modify in `app.py`:
- Price range slider limits
- Default BHK selection
- Possession year range

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
