import streamlit as st
import pandas as pd
import time
import os

st.set_page_config(page_title="NHIS Payments Dashboard", page_icon="🏥", layout="wide")

st.title("🏥 NHIS Payments Live Dashboard")
st.markdown("Monitor the scraper's progress in real-time.")

# Sidebar for controls
st.sidebar.header("Settings")
auto_refresh = st.sidebar.checkbox("Auto-Refresh", value=True)
refresh_rate = st.sidebar.slider("Refresh Interval (seconds)", 2, 30, 5)

def load_data():
    file_path = "nhis_payments_v2.csv"
    if os.path.exists(file_path):
        try:
            # We don't cache this so it updates instantly
            df = pd.read_csv(file_path)
            
            # Attempt to parse currency values for analytics
            if 'Amount Paid' in df.columns:
                df['Amount Paid Numeric'] = df['Amount Paid'].astype(str).str.replace(r'[^\d.]', '', regex=True)
                df['Amount Paid Numeric'] = pd.to_numeric(df['Amount Paid Numeric'], errors='coerce')
                
            return df
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

df = load_data()

if not df.empty:
    # Top Metrics
    total_records = len(df)
    total_amount = df['Amount Paid Numeric'].sum() if 'Amount Paid Numeric' in df.columns else 0
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Records Scraped", f"{total_records:,}")
    if total_amount > 0:
        m2.metric("Total Amount Paid Scraped (GHS)", f"{total_amount:,.2f}")
    m3.metric("Unique Districts", df['District'].nunique() if 'District' in df.columns else 0)

    st.divider()

    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Districts by Record Count")
        if 'District' in df.columns:
            st.bar_chart(df['District'].value_counts().head(10))
            
    with col2:
        st.subheader("Top 10 Districts by Amount Paid")
        if 'District' in df.columns and 'Amount Paid Numeric' in df.columns and total_amount > 0:
            district_sums = df.groupby('District')['Amount Paid Numeric'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(district_sums)

    # Data Table
    st.subheader("Latest Scraped Entries")
    # Show the last 100 rows in reverse order (newest first)
    st.dataframe(df.tail(100).iloc[::-1], use_container_width=True)

else:
    st.info("No data found yet. Start the scraper (main.py) to generate data.")

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
