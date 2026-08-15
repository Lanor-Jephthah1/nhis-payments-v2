from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

import json

app = FastAPI(title="NHIS Payments API")

# Configure CORS so our Vite frontend can fetch data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_PATH = r"C:\Users\Jephthah Kwame Lanor\Desktop\nhis\Lanor-Jephthah1-nhis-payments-scraper-edb31c8\nhis_payments_v2.csv"
STATUS_PATH = r"C:\Users\Jephthah Kwame Lanor\Desktop\nhis\Lanor-Jephthah1-nhis-payments-scraper-edb31c8\scraper_status.json"

@app.get("/api/status")
def get_scraper_status():
    if os.path.exists(STATUS_PATH):
        try:
            with open(STATUS_PATH, "r") as f:
                return json.load(f)
        except:
            return {"action": "Unknown", "progress": "Reading error", "detail": ""}
    return {"action": "Waiting", "progress": "No status file", "detail": "Start the scraper to see status."}

@app.get("/api/data")
def get_dashboard_data(page: int = 1, limit: int = 20, search: str = None, sort_by: str = None, order: str = "asc"):
    if not os.path.exists(CSV_PATH):
        return {"error": "CSV file not found yet. Is the scraper running?"}
        
    try:
        df = pd.read_csv(CSV_PATH)
        
        # Parse currency
        if 'Amount Paid' in df.columns:
            df['Amount Paid Numeric'] = df['Amount Paid'].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df['Amount Paid Numeric'] = pd.to_numeric(df['Amount Paid Numeric'], errors='coerce')
            
        # Clean up corrupted District data
        if 'District' in df.columns:
            df['District'] = df['District'].replace('#REF!', 'Unknown')
        
        # Metrics based on ALL data
        total_records = len(df)
        total_amount = df['Amount Paid Numeric'].sum() if 'Amount Paid Numeric' in df.columns else 0
        unique_districts = df['District'].nunique() if 'District' in df.columns else 0
        
        # Charts based on ALL data
        top_districts_count = df['District'].value_counts().head(10).to_dict() if 'District' in df.columns else {}
        top_districts_amount = {}
        if 'District' in df.columns and 'Amount Paid Numeric' in df.columns:
            top_districts_amount = df.groupby('District')['Amount Paid Numeric'].sum().sort_values(ascending=False).head(10).to_dict()
            
        # Add index
        df['_index'] = df.index + 1
        
        # Search/Filter
        if search:
            search = search.lower()
            mask = df['Facility Name'].astype(str).str.lower().str.contains(search) | \
                   df['District'].astype(str).str.lower().str.contains(search)
            df = df[mask]
            
        # Sorting
        if sort_by in ['Facility Name', 'District', 'Amount Paid Numeric']:
            ascending = (order == 'asc')
            df = df.sort_values(by=sort_by, ascending=ascending)
            
        # Pagination
        total_filtered = len(df)
        total_pages = max(1, (total_filtered + limit - 1) // limit)
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        paginated_df = df.iloc[start_idx:end_idx].fillna("")
        entries = paginated_df.to_dict(orient="records")
        
        return {
            "status": "success",
            "metrics": {
                "total_records": total_records,
                "total_amount": total_amount,
                "unique_districts": unique_districts
            },
            "charts": {
                "top_districts_count": top_districts_count,
                "top_districts_amount": top_districts_amount
            },
            "pagination": {
                "page": page,
                "limit": limit,
                "total_filtered": total_filtered,
                "total_pages": total_pages
            },
            "entries": entries
        }
        
    except Exception as e:
        return {"error": str(e)}

from fastapi.responses import StreamingResponse
import io

@app.get("/api/export")
def export_csv(search: str = None, sort_by: str = None, order: str = "asc"):
    if not os.path.exists(CSV_PATH):
        return {"error": "CSV file not found"}
        
    try:
        df = pd.read_csv(CSV_PATH)
        
        if 'Amount Paid' in df.columns:
            df['Amount Paid Numeric'] = df['Amount Paid'].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df['Amount Paid Numeric'] = pd.to_numeric(df['Amount Paid Numeric'], errors='coerce')
            
        if search:
            search = search.lower()
            mask = df['Facility Name'].astype(str).str.lower().str.contains(search) | \
                   df['District'].astype(str).str.lower().str.contains(search)
            df = df[mask]
            
        if sort_by in ['Facility Name', 'District', 'Amount Paid Numeric']:
            ascending = (order == 'asc')
            df = df.sort_values(by=sort_by, ascending=ascending)
            
        # Clean up for export
        if 'Amount Paid Numeric' in df.columns:
            df = df.drop(columns=['Amount Paid Numeric'])
            
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=nhis_export.csv"
        return response
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
