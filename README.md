# NHIS Payments Tracker v2

A robust, full-stack data pipeline and visualization dashboard for tracking National Health Insurance Scheme (NHIS) payments across districts in Ghana.

## Architecture

This project consists of three main components:

1. **Selenium Scraper (`/scraper`)**
   - **Language:** Python
   - **Framework:** Selenium WebDriver
   - **Features:** 
     - Automated headless browsing of the official NHIS payments portal.
     - Resilience engineering: Built-in retry mechanisms and staleness checks to handle server-side rate limiting, AJAX timeouts, and Cloudflare overlays.
     - Checkpoint recovery: Saves progress to `checkpoint.json` allowing the scraper to resume seamlessly after interruptions.
     - Data sanitization: Automatically cleans corrupted `#REF!` district rows dynamically inserted by the source ASP.NET table.

2. **Backend REST API (`/webapp/backend`)**
   - **Language:** Python
   - **Framework:** FastAPI / Pandas
   - **Features:**
     - In-memory Pandas dataframe operations for blazing-fast metric aggregations, sorting, and pagination.
     - Exposes paginated endpoints for the frontend to consume.
     - Streams CSV exports directly from memory.
     - Tunneled securely via Cloudflare (`cloudflared`) to bypass NAT and firewall restrictions for public consumption.

3. **Frontend Dashboard (`/webapp/frontend`)**
   - **Language:** HTML / CSS / Vanilla JavaScript
   - **Frameworks:** Chart.js
   - **Deployment:** Vercel
   - **Features:**
     - Modern, flat-design UI with responsive CSS Grid and Flexbox layouts.
     - Dynamic Chart.js integration mapping real-time data from the backend tunnel.
     - Fully optimized Open Graph SEO tags for WhatsApp/Twitter link unfurling.

## Demo

Check out the live scraping and dashboard rendering in action:

![Demo](./demo.gif)

## Setup & Local Development

### Requirements
- Python 3.10+
- Node.js (for Vercel CLI)
- Google Chrome & ChromeDriver

### Running the Scraper
```bash
cd scraper
python main.py
```
This will launch the scraper, generate `nhis_payments_v2.csv`, and track progress in `checkpoint.json`.

### Running the API
```bash
cd webapp/backend
pip install fastapi uvicorn pandas
python main.py
```
This will expose the API at `http://127.0.0.1:8000`.

### Exposing the API publicly (Cloudflare Tunnel)
```bash
cd webapp/backend
cloudflared tunnel --url http://127.0.0.1:8000
```
*Note: Update `webapp/frontend/main.js` with the new generated Cloudflare URL.*

### Running the Frontend
```bash
cd webapp/frontend
npx vercel --prod
```

## Future Enhancements
- Dockerize the entire stack for simple one-click deployment.
- Integrate PostgreSQL to replace the in-memory Pandas dataframe for long-term data persistence.
- Add cron jobs to fully automate the scraper schedule on a VPS.

## Author
**Jephthah Kwame Lanor**
- GitHub: [@Lanor-Jephthah1](https://github.com/Lanor-Jephthah1)
- Twitter: [@jeff_lanor](https://twitter.com/jeff_lanor)

## License
This project is open-source and available under the [MIT License](LICENSE).
