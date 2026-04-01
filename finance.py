import streamlit as st
import yfinance as yf
import plotly.express as px
import PyPDF2
from google import genai

API_KEY = st.secrets["GEMINI_API_KEY"]

st.title("📊 Company Financial Analyzer")
st.subheader("Live Data + Annual Report AI Analysis")

tab1, tab2 = st.tabs(["🏢 Live Company Data", "📄 Annual Report Analysis"])

with tab1:
    st.write("Examples: TCS.NS, INFY.NS, WIPRO.NS, ACN (Accenture)")
    company = st.text_input("Enter Company Ticker Symbol")
    if company and st.button("🔍 Fetch Financial Data"):
        try:
            ticker = yf.Ticker(company)
            info = ticker.info
            st.metric("Company", info.get('longName', company))
            st.metric("Revenue", f"${info.get('totalRevenue', 0):,}")
            st.metric("Net Profit", f"${info.get('netIncomeToCommon', 0):,}")
            st.metric("Profit Margin", f"{info.get('profitMargins', 0)*100:.1f}%")
            st.metric("Operating Margin", f"{info.get('operatingMargins', 0)*100:.1f}%")
            hist = ticker.history(period="1y")
            fig = px.line(hist, x=hist.index, y='Close', title=f"{company} - 1 Year Stock Trend")
            st.plotly_chart(fig)
        except Exception as e:
            st.error(f"Error fetching data. Please check ticker symbol. {e}")

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
                client = genai.Client(api_key=API_KEY)
                prompt = f"You are a CMA analyst. From this annual report extract: 1) Key costs 2) Revenue trends 3) Profit margins 4) 3 strategic recommendations:\n\n{text[:3000]}"
                response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                st.success(response.text)
            except Exception as e:
                st.error(f"Error: {e}")