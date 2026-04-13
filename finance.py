import streamlit as st
import yfinance as yf
import plotly.express as px
import PyPDF2
from groq import Groq
import requests
import time

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

st.title("📊 Company Financial Analyzer")
st.subheader("Live Data + Annual Report AI Analysis")

tab1, tab2, tab3 = st.tabs(["🏢 Live Company Data", "📄 Annual Report Analysis", "🔍 Find Ticker Symbol"])

with tab3:
    st.subheader("🔍 Find Any Company's Ticker Symbol")
    st.write("Don't know the ticker? Search by company name!")

    search_name = st.text_input("Type company name (e.g. Reliance, Infosys, Apple, Ford Motors)")

    if search_name:
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={search_name}&quotesCount=10&newsCount=0&enableFuzzyQuery=true"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=5)
            data = response.json()
            quotes = [q for q in data.get("quotes", []) if q.get("symbol")]

            if quotes:
                st.success(f"✅ Found {len(quotes)} results:")
                for q in quotes:
                    name = q.get("shortname") or q.get("longname") or q.get("symbol")
                    symbol = q.get("symbol")
                    exchange = q.get("exchange", "")
                    st.code(f"{name} ({exchange}) → {symbol}")
            else:
                st.warning("No results found. Try a different spelling.")
        except Exception as e:
            st.error(f"Search failed: {e}")

    st.divider()
    st.subheader("📋 Complete Ticker Reference Table")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🇮🇳 Top Indian Companies (NSE)**")
        st.markdown("""
| Company | Ticker |
|---------|--------|
| Reliance | RELIANCE.NS |
| TCS | TCS.NS |
| Infosys | INFY.NS |
| HDFC Bank | HDFCBANK.NS |
| ICICI Bank | ICICIBANK.NS |
| Wipro | WIPRO.NS |
| SBI | SBIN.NS |
| L&T | LT.NS |
| ITC | ITC.NS |
| Bajaj Finance | BAJFINANCE.NS |
| Asian Paints | ASIANPAINT.NS |
| Maruti | MARUTI.NS |
| Sun Pharma | SUNPHARMA.NS |
| Tech Mahindra | TECHM.NS |
| Tata Motors | TATAMOTORS.NS |
        """)

    with col2:
        st.markdown("**🌍 Top Global Companies**")
        st.markdown("""
| Company | Ticker |
|---------|--------|
| Accenture | ACN |
| Apple | AAPL |
| Microsoft | MSFT |
| Google | GOOGL |
| Amazon | AMZN |
| Tesla | TSLA |
| Meta | META |
| Netflix | NFLX |
| JP Morgan | JPM |
| Goldman Sachs | GS |
| IBM | IBM |
| Oracle | ORCL |
| SAP | SAP |
| Ford | F |
| Toyota | TM |
        """)

    st.info("💡 **Tip:** For BSE listed companies add .BO instead of .NS  \nExample: RELIANCE.BO")

with tab1:
    st.write("💡 Don't know the ticker? Check the **Find Ticker Symbol** tab!")
    company = st.text_input("Enter Company Ticker Symbol (e.g. TCS.NS, INFY.NS, ACN)")

    if company and st.button("🔍 Fetch Financial Data"):
        with st.spinner("Fetching data... please wait"):
            info = None
            hist = None
            error = None
            for attempt in range(3):
                try:
                    ticker = yf.Ticker(company)
                    info = ticker.info
                    hist = ticker.history(period="1y")
                    break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(3 * (attempt + 1))
                    else:
                        error = str(e)

        if error:
            st.error("⚠️ Yahoo Finance rate limited. Wait 30–60 seconds and try again.")
            st.info("💡 Tip: Try a different ticker or come back in a minute.")
        else:
            st.metric("Company", info.get('longName', company))
            st.metric("Revenue", f"${info.get('totalRevenue', 0):,}")
            st.metric("Net Profit", f"${info.get('netIncomeToCommon', 0):,}")
            st.metric("Profit Margin", f"{info.get('profitMargins', 0)*100:.1f}%")
            st.metric("Operating Margin", f"{info.get('operatingMargins', 0)*100:.1f}%")

            if hist is not None and not hist.empty:
                fig = px.line(hist, x=hist.index, y='Close', title=f"{company} - 1 Year Stock Trend")
                st.plotly_chart(fig)
            else:
                st.warning("No stock history found. Please check the ticker symbol.")

with tab2:
    st.write("Upload a company's Annual Report PDF for AI analysis")
    pdf_file = st.file_uploader("📁 Upload Annual Report PDF", type="pdf")
    if pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages[:10]:
            text += page.extract_text()
        st.success(f"✅ Read {len(reader.pages)} pages successfully!")
        if st.button("🤖 Analyze Report"):
            try:
                client = Groq(api_key=GROQ_API_KEY)
                prompt = f"You are a CMA analyst. From this annual report extract: 1) Key costs 2) Revenue trends 3) Profit margins 4) 3 strategic recommendations:\n\n{text[:3000]}"
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.success(response.choices[0].message.content)
            except Exception as e:
                st.error(f"Error: {e}")
