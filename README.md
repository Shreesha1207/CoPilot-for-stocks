# Stock Copilot AI

This is a modern, AI-powered stock analysis tool built with Streamlit.

## Features
- **Real-time Stock Data**: View live prices, charts, and financial metrics using Yahoo Finance.
- **Interactive Charts**: Zoomable and pannable candlestick charts.
- **AI Copilot**: Chat with an AI financial analyst powered by Google Gemini to get insights on any stock.
- **Financials**: Deep dive into income statements and key ratios.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the App**:
    ```bash
    streamlit run "Cosmocloud Hackathon/streamlit_app.py"
    ```

3.  **API Key**:
    -   Get your Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey).
    -   Open the `.env` file in the project root.
    -   Replace `YOUR_API_KEY_HERE` with your actual key:
        ```
        GOOGLE_API_KEY=AIzaSy...
        ```

## Note
The old Flask app (`app.py`) is still available but the new Streamlit app provides a much richer experience.
