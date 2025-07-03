from flask import Flask, render_template, request
import requests, pandas as pd
from functools import lru_cache
from datetime import datetime
import random
import os

app = Flask(__name__)

@lru_cache(maxsize=1)
def fetch_opensky_data():
    try:
        response = requests.get("https://opensky-network.org/api/states/all", timeout=5)
        return response.json()
    except Exception as e:
        print("Error fetching OpenSky data:", e)
        return {"states": []}

def generate_price_trends(countries):
    currency_map = {
        'United States': 'USD', 'India': 'INR', 'Australia': 'AUD', 'Germany': 'EUR',
        'France': 'EUR', 'United Kingdom': 'GBP', 'Canada': 'CAD', 'Japan': 'JPY',
        'China': 'CNY', 'Brazil': 'BRL'
    }
    trends = {}
    for country in countries:
        price = random.randint(200, 800)
        currency = currency_map.get(country, 'USD')
        trends[country] = f"{price} {currency}"
    return trends

@app.route('/.well-known/<path:subpath>')
def handle_well_known(subpath):
    return '', 204

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/results', methods=['GET'])
def results():
    data = fetch_opensky_data()
    states = data.get('states', [])[:300]

    df = pd.DataFrame(states, columns=[
        "icao24", "callsign", "origin_country", "time_position",
        "last_contact", "longitude", "latitude", "baro_altitude",
        "on_ground", "velocity", "true_track", "vertical_rate",
        "sensors", "geo_altitude", "squawk", "spi", "position_source"
    ])

    df = df.dropna(subset=['origin_country'])
    df['callsign'] = df['callsign'].fillna("N/A")

    selected_country = request.args.get('country')
    if selected_country:
        df = df[df['origin_country'] == selected_country]

    top_routes = df['origin_country'].value_counts().head(5).to_dict()
    price_trends = generate_price_trends(top_routes.keys())
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return render_template('results.html',
        top_routes=top_routes,
        price_trends=price_trends,
        table=df.to_html(classes='table table-striped', index=False),
        selected_country=selected_country,
        countries=sorted(df['origin_country'].unique()),
        last_updated=last_updated
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)