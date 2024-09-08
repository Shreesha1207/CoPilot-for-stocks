from flask import Flask, render_template, request
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def get_stock_info(stock_symbol, period='1d', interval='1m'):
    # Create a Ticker object
    stock = yf.Ticker(stock_symbol)
    hist = stock.history(period=period, interval=interval)

    if hist.empty or 'Close' not in hist.columns:
        return None, False, 0, None  # Return 0 rating and no graph if no data is available
    
    # Extract the latest closing price safely
    stock_price = hist['Close'].iloc[-1] if not hist.empty else None
    
    if stock_price is None:
        return None, False, 0, None  # Handle cases where no stock price is available

    
    # Extract the latest closing price
    stock_price = hist['Close'].iloc[-1]
    
    # Calculate the rating based on the past month
    month_hist = stock.history(period='1mo', interval='1d')
    if month_hist.empty:
        rating = 0
    else:
        # Calculate stock performance over the past month
        month_performance = (stock_price - month_hist['Close'].iloc[0]) / month_hist['Close'].iloc[0] * 100

        # Determine stability based on volatility over the past month
        stability = month_hist['Close'].std()  # Standard deviation as a measure of volatility
        
        # Calculate a basic rating
        rating = 5  # Start with a base rating of 5
        
        # Increase rating based on positive performance
        if month_performance > 0:
            rating += min(3, month_performance / 10)  # Cap the increase to 3 points
        
        # Decrease rating for high volatility (less stable)
        if stability > stock_price * 0.05:  # Consider a stock volatile if its std dev > 5% of price
            rating -= min(2, stability / stock_price * 20)  # Cap the decrease to 2 points
        
        # Adjust rating based on top investor interest
        top_investors_interested = stock_symbol in ['AAPL', 'MSFT', 'GOOGL']
        if top_investors_interested:
            rating += 1  # Increase rating if top investors are interested
        
        # Ensure the rating is between 1 and 10
        rating = max(1, min(10, rating))
        
        # Round the rating to 1 decimal place
        rating = round(rating, 1)
    
    # Generate the performance graph based on the selected period
    graph = generate_graph(hist, period)
    return stock_price, top_investors_interested, rating, graph

def generate_graph(hist, period):
    plt.figure(figsize=(10, 5))
    plt.plot(hist.index, hist['Close'], label='Close Price')

    # Format the x-axis based on the selected period
    if period == '1d':
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))  # Hour:Minute format
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.HourLocator(interval=1))  # Major ticks every hour
    elif period == '5d':
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %d'))  # Month Day format
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.DayLocator(interval=1))  # Major ticks every day
    elif period == '1mo':
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %d'))  # Month Day format
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.WeekdayLocator(interval=1))  # Major ticks every week

    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title(f'Stock Performance Over {period}')
    plt.legend()
    
    # Rotate date labels for better readability
    plt.gcf().autofmt_xdate()

    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Encode the image to base64
    graph = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return graph


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        stock_symbol = request.form['stock'].upper()
        
        # For Yahoo Finance, you might need to use '.NS' for NSE stocks or '.BO' for BSE stocks
        if stock_symbol in ['RELIANCE', 'TCS', 'INFY']:
            stock_symbol += '.NS'
        
        # Default period and interval
        period = '1d'
        interval = '1m'
        
        stock_price, top_investors, rating, graph = get_stock_info(stock_symbol, period=period, interval=interval)
        stock_price=round(stock_price,3)
        
        if stock_price:
            return render_template("result.html", stock=stock_symbol, price=stock_price, top_investors=top_investors, rating=rating, graph=graph, period=period)
        else:
            error_message = "Could not retrieve data for the stock symbol provided. Please check the symbol and try again."
            return render_template('index.html', error=error_message)
            
    return render_template('index.html')

@app.route('/result', methods=['GET', 'POST'])
@app.route('/result/<stock>', methods=['GET', 'POST'])
def result(stock):
    period = request.args.get('period')
    
    # Set interval based on the period selected
    if period == '1d':
        interval = '30m'  # 30 minutes interval for 1 day
    elif period == '1wk':
        period='5d'
        interval = '1h'  # 1-hour interval for 5 days
    elif period == '1mo':
        interval = '1d'  # 1-day interval for 1 month
    else:
        interval = '1d'  # Default to 1-day interval if unknown period
    
    stock_price, top_investors, rating, graph = get_stock_info(stock, period=period, interval=interval)
    
    # Check for NoneType before rounding
    if stock_price is not None:
        stock_price = round(stock_price, 3)
    else:
        error_message = "Could not retrieve data for the stock symbol provided. Please check the symbol and try again."
        return render_template('index.html', error=error_message)
    
    return render_template('result.html', stock=stock, price=stock_price, top_investors=top_investors, rating=rating, graph=graph, period=period)


# @app.route('/update', methods=['POST'])
# def update():
#     stock_symbol = request.form['stock']
#     period = request.form['period']
    
#     # Set interval based on the selected period
#     if period == '1d':
#         interval = '30m'  # 30 minutes interval for 1 day period
#     elif period == '1wk':
#         interval = '1d'  # 1 hour interval for 1 week period
#     else:
#         interval = '1wk'  # 1 day interval for 1 month period
    
#     stock_price, top_investors, rating, graph = get_stock_info(stock_symbol, period=period, interval=interval)
#     stock_price = round(stock_price, 3)
    
#     if stock_price:
#         return render_template('result.html', stock=stock_symbol, price=stock_price, top_investors=top_investors, rating=rating, graph=graph, period=period)
#     else:
#         error_message = "Could not retrieve data for the stock symbol provided. Please check the symbol and try again."
#         return render_template('index.html', error=error_message)


if __name__ == '__main__':
    app.run(debug=True)
