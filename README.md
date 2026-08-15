# NHIS Payments Tracker (Version 2)

A robust, full-stack application designed to automatically scrape, process, and visualize payment data from the Ghana National Health Insurance Scheme (NHIS) portal.

## Architecture

This project is divided into two primary components:

1. **Scraper Engine (`/scraper`)**
   - Built with Python and Selenium WebDriver.
   - Bypasses ASP.NET strict-mode protections to achieve high-speed pagination skipping via JavaScript injection.
   - Resilient state-machine design capable of recovering from network failures.
   - Outputs structured data into CSV format and maintains a live `scraper_status.json` file for real-time monitoring.

2. **Web Dashboard (`/webapp`)**
   - **Backend API**: A high-performance FastAPI server that parses the scraped CSV data, aggregates metrics (Top Districts, Total Payouts), and handles dynamic search, sorting, and pagination.
   - **Frontend UI**: A responsive, modern interface built with vanilla HTML/CSS/JS. Features live real-time scraper monitoring, data sorting, search filtering, and instant CSV exports.

## Key Features

- **Automated Data Extraction**: Extracts thousands of records systematically without manual intervention.
- **Real-Time Monitoring**: The dashboard displays live updates on the scraper's progress, including current page, action status, and detailed logs.
- **Dynamic Data Visualization**: Interactive table with column sorting (Facility Name, District, Amount Paid).
- **Search & Filtering**: Real-time debounced search across all scraped records.
- **Data Export**: One-click export of currently filtered data to CSV.

## Getting Started

### Prerequisites
- Python 3.9+
- Google Chrome & ChromeDriver

### Installation

1. Install backend and scraper dependencies:
   ```bash
   pip install selenium webdriver-manager rich pandas fastapi uvicorn
   ```

2. Start the FastAPI Backend:
   ```bash
   cd webapp/backend
   python main.py
   ```

3. Launch the Frontend:
   Serve the `webapp/frontend` directory using any local web server. For example:
   ```bash
   cd webapp/frontend
   python -m http.server 8080
   ```
   Access the dashboard at `http://localhost:8080`.

4. Run the Scraper (in a separate terminal):
   ```bash
   cd scraper
   python main.py --headless
   ```

## Deployment Strategy

For production deployment, the recommended architecture is:
- **Frontend**: Host the static assets on Vercel or Netlify.
- **Backend API**: Host the FastAPI server on Render.com.
- **Scraper Pipeline**: Configure a GitHub Actions cron job to run the scraper periodically and sync the updated CSV data to an AWS S3 bucket.

## License

This project is open-source and available under the MIT License.
