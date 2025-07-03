from flask import Flask, render_template, request
import requests
import pandas as pd
from datetime import datetime

app = Flask(__name__)

def get_flight_data():
    url = "https://opensky-network.org/api/states/all"
    try:
        response = requests.get(url, timeout=10)  
        response.raise_for_status() 
        data = response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        print("Error fetching data:", e)
        return pd.DataFrame([])

    flights = []
    for item in data.get('states', [])[:100]:  # Limit to 100 records
        time_value = item[4]
        if time_value and isinstance(time_value, (int, float)):
            time_str = datetime.utcfromtimestamp(time_value).strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = "N/A"

        flights.append({
            'callsign': item[1] or 'N/A',
            'origin_country': item[2],
            'longitude': item[5],
            'latitude': item[6],
            'velocity': item[9],
            'time': time_str
        })

    return pd.DataFrame(flights)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/results')
def results():
    selected_country = request.args.get('country')

    df = get_flight_data()

    if df.empty:
        return "⚠️ Unable to fetch data at this time."

    if selected_country:
        df = df[df['origin_country'] == selected_country]

    # Get top 5 countries for chart
    top_routes = df['origin_country'].value_counts().head(5).to_dict()

    return render_template(
        'results.html',
        top_routes=top_routes,
        table=df.to_html(classes='table table-striped', index=False),
        selected_country=selected_country,
        countries=sorted(df['origin_country'].dropna().unique()),
        last_updated=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    )

if __name__ == '__main__':
    app.run(debug=True)
