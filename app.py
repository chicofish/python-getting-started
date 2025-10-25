# app.py - FastAPI Application

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # <-- ADD THIS IMPORT
import yfinance as yf
import pandas as pd
import numpy as np

app = FastAPI(title="401k Portfolio Data API")

# Define the specific origin of your Live Server
LIVE_SERVER_ORIGIN = "http://127.0.0.1:5500"

# In development, you can use ["*"] to allow all origins.
# In production, list only the origins that need access (e.g., ["https://yourdomain.com"]).
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:5500", # <-- Specifically add the live server port!
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[LIVE_SERVER_ORIGIN],  # Allows all origins for simplicity in development
    # Note: If you use the 'origins' list above, change this to `allow_origins=origins`
    allow_credentials=False,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Core Data and Logic (from your notebook) ---

investment_options = [
    # Core Equity
    "DODGX", "FLCSX", "FXAIX", "VFIAX", "VFINX", "TRBCX", "PRGFX",
    # Target-Date
    "VTTVX", "VTTSX", "VTIVX", "VFFVX", "VSVNX", "TRRKX", "FFTHX",
    # Bond/Fixed-Income
    "FTBFX", "VBTLX", "VBMFX", "VIPIX", "MWTSX", "PTTRX",
    # Balanced/Specialty
    "PRWCX", "VWELX", "FCNTX", "DODFX",
    # International Large-Cap
    "VGTSX", "VTIAX", "FSPSX", "VFWAX", "TRIGX",
    # International Small-Cap
    "VFSVX", "VFSAX", "FISMX", "VINEX",
    # Emerging Markets
    "VEMAX", "FPADX",
]

market_indexes = [
    '^VIX', '^MOVE', '^GSPC', '^TNX', '^IRX', 'TIP'
]

def get_cleaned_data():
    """
    Fetches raw data using yfinance and processes it to create the clean_df.
    """
    
    # 1. Fetch historical price data
    try:
        data = yf.download(
            investment_options + market_indexes, 
            start="1995-01-01", 
            end="2025-10-24"
        )["Close"]
    except Exception as e:
        print(f"Error fetching data: {e}. Generating dummy data.")
        # 2. Fallback to dummy data (as in your notebook)
        np.random.seed(42)
        dates = pd.date_range(start="2025-01-01", end="2025-09-29", freq="B")
        data = pd.DataFrame(
            {ticker: 100 * np.exp(np.cumsum(np.random.normal(0.0002, 0.01, len(dates))))
             for ticker in investment_options + market_indexes}, index=dates
        )
    
    # 3. Getting data starting with the ticker with most recent values (2022-07-05)
    # Note: Using .loc is inclusive of the end date, but yfinance end date is exclusive.
    # The actual data fetching will determine the true max date.
    most_recent = data.loc['2022-07-05':]

    # 4. Drop the VFSVX column (as VFSVX had 831 null values in the 'most_recent' slice)
    # Also drop rows with any remaining NaNs for robustness
    clean_df = most_recent.drop(columns=['VFSVX']).dropna() 
    
    return clean_df

# --- API Endpoint ---

@app.get("/get-401k-data")
async def api_get_401k_data():
    """
    Returns the cleaned 401k portfolio and index data.
    """
    try:
        clean_df = get_cleaned_data()
        
        # Convert DataFrame to a format easily consumed by a web app (e.g., records or json)
        # 'orient="records"' returns a list of dictionaries (one dict per row)
        data_json = clean_df.to_dict(orient="records")
        
        return JSONResponse(
            content={
                "status": "success",
                "message": "401k portfolio data fetched and cleaned.",
                "data": data_json,
                "row_count": len(clean_df)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"An error occurred: {str(e)}"}
        )

# Optional: Root endpoint for health check
@app.get("/")
def read_root():
    return {"Hello": "Welcome to the 401k Data API. Use /get-401k-data to fetch the data."}