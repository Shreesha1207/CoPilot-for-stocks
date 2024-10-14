import os
from flask import Flask, render_template, request
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64
import google.generativeai as genai
import pymongo

app = Flask(__name__)

# Fetch the API Key
genai.configure(api_key="AIzaSyAcsU2OPwlK7mDeIVxvO6eIB5bDew2ZxdQ")

# Connect to MongoDB
client=pymongo.MongoClient("mongodb+srv://shreeshamr:Fk6zmcIOUcQJuSro@clusterforstocks.b2yrq.mongodb.net/?retryWrites=true&w=majority&appName=Clusterforstocks")
  # Use your MongoDB connection URI
db = client['copilotforstocks']  # Replace with your database name
popular_stocks_collection = db['popular stocks']  # Replace with your collection name

def get_stock_info(stock_symbol, period='1d', interval='1m'):
    # Create a Ticker object
    stock = yf.Ticker(stock_symbol)
    hist = stock.history(period=period, interval=interval)

    if hist.empty or 'Close' not in hist.columns:
        return None, 0, None  # Return 0 rating and no graph if no data is available

    # Extract the latest closing price safely
    stock_price = hist['Close'].iloc[-1]

    # Get rating from AI
    rating = get_stock_rating_from_gemini(stock_symbol, period, interval)

    # Generate the performance graph based on the selected period
    graph = generate_graph(hist, period)

    return stock_price, rating, graph

def get_stock_rating_from_gemini(stock_symbol, period, interval):
    stock = yf.Ticker(stock_symbol)
    hist = stock.history(period=period, interval=interval)

    # Get the income statement instead of earnings
    income_stmt = stock.income_stmt

    if income_stmt is None:
        return 0.0  # Handle missing financial data

    net_income = income_stmt.get('Net Income', 0)
    eps = income_stmt.get('Earnings Per Share', 0)

    # Get balance sheet info safely
    balance_sheet = stock.balance_sheet

    if balance_sheet is not None:
        total_revenue = balance_sheet.get('Total Revenue', 0)
        total_liabilities = balance_sheet.get('Total Liabilities', 0)
        stockholder_equity = balance_sheet.get('Stockholder Equity', 0)

        # Calculate financial ratios
        if total_revenue and stockholder_equity and total_liabilities:
            profit_margin = net_income / total_revenue
            debt_equity_ratio = total_liabilities / stockholder_equity
        else:
            profit_margin = 0
            debt_equity_ratio = 0
    else:
        profit_margin = 0
        debt_equity_ratio = 0

    # Gather additional financial data
    info = stock.info

    industry = info.get('industry', 'N/A')
    market_cap = info.get('marketCap', 0)
    pe_ratio = info.get('trailingPE', 0)

    # Update the prompt with specific data
    prompt = f"""
    Evaluate stock {stock_symbol} based on:
    - EPS: {eps}
    - Profit Margin: {profit_margin}
    - Debt-to-Equity Ratio: {debt_equity_ratio}
    - Industry: {industry}
    - Market Cap: {market_cap}
    - P/E Ratio: {pe_ratio}

    Provide a rating between 1 and 10. Just give the rating(number). Do not explain the rating.
    """

    # Call the Gemini API to generate content
    model = genai.GenerativeModel("gemini-1.5-flash")
    try:
        response = model.generate_content(prompt)

        # Check if response has a 'result' attribute
        if hasattr(response, 'result'):
            rating_text = response.result.candidates[0].content.parts[0].text.strip()
            rating = float(rating_text)
            return round(rating, 1)
        elif hasattr(response, 'candidates'):
            # If 'result' is missing, try accessing 'candidates' directly
            rating_text = response.candidates[0].content.parts[0].text.strip()
            rating = float(rating_text)
            return round(rating, 1)
        else:
            print("Error: Unable to extract rating from response.")
            return 0.0  # Handle the error gracefully
    except Exception as e:
        print(f"Error: {e}")
        return 0.0

def generate_graph(hist, period):
    plt.figure(figsize=(10, 5))
    plt.plot(hist.index, hist['Close'], label='Close Price')

    # Format the x-axis based on the selected period
    if period == '1d':
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.HourLocator(interval=1))
    elif period == '5d':
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %d'))
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.DayLocator(interval=1))
    elif period == '1mo':
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %d'))
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.WeekdayLocator(interval=1))

    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title(f'Stock Performance Over {period}')
    plt.legend()

    # Rotate date labels for better readability
    plt.gcf().autofmt_xdate()

    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()  # Close the figure to free memory
    buf.seek(0)

    # Encode the image to base64
    graph = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return graph

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        stock_symbol = request.form['stock'].upper()

        # Retrieve popular stocks from MongoDB
        popular_stock = popular_stocks_collection.find({'symbol': stock_symbol})

        # For Yahoo Finance, you might need to use '.NS' for NSE stocks or '.BO' for BSE stocks
        if popular_stock and stock_symbol in ['RELIANCE', 'TCS', 'INFY']:
            stock_symbol += '.NS'
        # Default period and interval
        period = '1d'
        interval = '1m'

        stock_price, rating, graph = get_stock_info(stock_symbol, period=period, interval=interval)

        if stock_price:
            stock_price = round(stock_price, 3)
            return render_template("result.html", stock=stock_symbol, price=stock_price, rating=rating, graph=graph, period=period)
        else:
            error_message = "Could not retrieve data for the stock symbol provided. Please check the symbol and try again."
            return render_template('index.html', error=error_message)

    return render_template('index.html')

@app.route('/result/<stock>', methods=['GET', 'POST'])
def result(stock):
    period = request.args.get('period', '1d')

    # Set interval based on the period selected
    if period == '1d':
        interval = '30m'  # 30 minutes interval for 1 day
    elif period == '1wk':
        period = '5d'
        interval = '1h'  # 1-hour interval for 5 days
    elif period == '1mo':
        interval = '1d'  # 1-day interval for 1 month
    else:
        interval = '1d'  # Default to 1-day interval if unknown period

    stock_price, rating, graph = get_stock_info(stock, period=period, interval=interval)

    if stock_price is not None:
        stock_price = round(stock_price, 3)
        return render_template('result.html', stock=stock, price=stock_price, rating=rating, graph=graph, period=period)
    else:
        error_message = "Could not retrieve data for the stock symbol provided. Please check the symbol and try again."
        return render_template('index.html', error=error_message,rating=rating)

if __name__ == '__main__':
    app.run(debug=True)
