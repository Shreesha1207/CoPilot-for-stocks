from flask import Flask, render_template, request, redirect, url_for
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Get popular stocks (e.g., from Yahoo Finance)
POPULAR_STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX']

def get_stock_info(stock_symbol, period='1d', interval='1m'):
    stock = yf.Ticker(stock_symbol)
    hist = stock.history(period=period, interval=interval)

    if hist.empty:
        return None, False, 0, None
    
    stock_price = hist['Close'].iloc[-1]
    month_hist = stock.history(period='1mo', interval='1d')
    if month_hist.empty:
        rating = 0
    else:
        month_performance = (stock_price - month_hist['Close'].iloc[0]) / month_hist['Close'].iloc[0] * 100
        stability = month_hist['Close'].std()
        rating = 5
        if month_performance > 0:
            rating += min(3, month_performance / 10)
        if stability > stock_price * 0.05:
            rating -= min(2, stability / stock_price * 20)
        
        top_investors_interested = stock_symbol in ['AAPL', 'MSFT', 'GOOGL']
        if top_investors_interested:
            rating += 1

        rating = max(1, min(10, round(rating, 1)))
    
    graph = generate_graph(hist, period)
    return stock_price, top_investors_interested, rating, graph

def generate_graph(hist, period):
    plt.figure(figsize=(10, 5))
    plt.plot(hist.index, hist['Close'], label='Close Price')

    if period == '1d':
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.HourLocator(interval=1))
    elif period == '1wk':
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %d'))
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.DayLocator(interval=1))
    elif period == '1mo':
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %d'))
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.WeekdayLocator(interval=1))

    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title(f'Stock Performance Over {period}')
    plt.legend()
    plt.gcf().autofmt_xdate()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return graph

@app.route('/get_stock/<stock_symbol>', methods=['GET'])
def get_stock(stock_symbol):
    # Default period and interval for popular stock
    period = '1d'
    interval = '1m'
    
    stock_price, top_investors, rating, graph = get_stock_info(stock_symbol, period=period, interval=interval)
    stock_price = round(stock_price, 3)

    if stock_price:
        return render_template('result.html', stock=stock_symbol, price=stock_price, top_investors=top_investors, rating=rating, graph=graph, period=period)
    else:
        error_message = "Could not retrieve data for the stock symbol provided."
        return render_template('index.html', error=error_message)

@app.route('/update', methods=['POST'])
def update():
    stock_symbol = request.form['stock']
    period = request.form['period']
    
    # Set interval based on the selected period
    if period == '1d':
        interval = '30m'  # 30 minutes interval for 1 day period
    elif period == '1wk':
        interval = '1h'  # 1 hour interval for 1 week period
    else:
        interval = '1d'  # 1 day interval for 1 month period
    
    stock_price, top_investors, rating, graph = get_stock_info(stock_symbol, period=period, interval=interval)
    
    # Check if stock_price is None before rounding
    if stock_price is not None:
        stock_price = round(stock_price, 3)
    else:
        # Return an error if no data was returned for the specified period/interval
        error_message = f"No data available for {stock_symbol} for the period: {period}."
        return render_template('index.html', error=error_message)
    
    # If valid data is returned, render the result page
    if stock_price:
        return render_template('result.html', stock=stock_symbol, price=stock_price, top_investors=top_investors, rating=rating, graph=graph, period=period)
    else:
        error_message = "Could not retrieve data for the stock symbol provided. Please check the symbol and try again."
        return render_template('index.html', error=error_message)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        stock_symbol = request.form['stock'].upper()
        if stock_symbol in ['RELIANCE', 'TCS', 'INFY']:
            stock_symbol += '.NS'
        return redirect(url_for('result', stock=stock_symbol, period='1d'))
    
    return render_template('index.html', popular_stocks=POPULAR_STOCKS)

@app.route('/result/<stock>', methods=['GET', 'POST'])
def result(stock):
    period = request.args.get('period', '1d')  # Get the selected period from the request
    interval = '1m' if period == '1d' else '1d'  # Adjust the interval based on the period
    stock_price, top_investors, rating, graph = get_stock_info(stock, period=period, interval=interval)
    stock_price = round(stock_price, 3)

    if stock_price:
        return render_template('result.html', stock=stock, price=stock_price, top_investors=top_investors, rating=rating, graph=graph, period=period)
    else:
        error_message = "Could not retrieve data for the stock symbol provided. Please check the symbol and try again."
        return render_template('index.html', error=error_message)

if __name__ == '__main__':
    app.run(debug=True)
