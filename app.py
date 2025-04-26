import logging
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

CACHE_FILE = 'cached_showtimes.json'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NYC Movie Theaters with addresses and URLs
theaters = [
    {"name": "AMC Empire 25", "address": "234 W 42nd St, New York, NY 10036", "url": "https://feverup.com/movies/en/united-states/movie-theaters/amc-empire-25"},
    {"name": "AMC 84th Street 6", "address": "2310 Broadway, New York, NY 10024", "url": "https://feverup.com/movies/en/united-states/movie-theaters/amc-84th-street-6"},
    {"name": "AMC Orpheum 7", "address": "1538 Third Ave, New York, NY 10028", "url": "https://feverup.com/movies/en/united-states/movie-theaters/amc-orpheum-7"},
    {"name": "AMC Village 7", "address": "66 Third Ave, New York, NY 10003", "url": "https://feverup.com/movies/en/united-states/movie-theaters/amc-village-7"},
    {"name": "AMC 19th St. East 6", "address": "890 Broadway, New York, NY 10003", "url": "https://feverup.com/movies/en/united-states/movie-theaters/amc-19th-st-east-6"},
    {"name": "AMC Lincoln Square 13", "address": "1998 Broadway, New York, NY 10023", "url": "https://feverup.com/movies/en/united-states/movie-theaters/amc-lincoln-square-13"},
    {"name": "AMC 34th Street 14", "address": "312 W 34th St, New York, NY 10001", "url": "https://feverup.com/movies/en/united-states/movie-theaters/amc-34th-street-14"},
    {"name": "AMC Kips Bay 15", "address": "570 Second Ave, New York, NY 10016", "url": "https://feverup.com/movies/en/united-states/movie-theaters/amc-kips-bay-15"},
    {"name": "AMC Magic Johnson Harlem 9", "address": "2309 Frederick Douglass Blvd, New York, NY 10027", "url": "https://feverup.com/movies/en/united-states/movie-theaters/amc-magic-johnson-harlem-9"},
    {"name": "Regal Union Square", "address": "850 Broadway, New York, NY 10003", "url": "https://feverup.com/movies/en/united-states/movie-theaters/regal-union-square"},
    {"name": "Regal Essex Crossing", "address": "129 Delancey St, New York, NY 10002", "url": "https://feverup.com/movies/en/united-states/movie-theaters/regal-essex-crossing"},
    {"name": "Regal Times Square", "address": "247 W 42nd St, New York, NY 10036", "url": "https://feverup.com/movies/en/united-states/movie-theaters/regal-e-walk"},
    {"name": "Regal Battery Park", "address": "102 North End Ave, New York, NY 10282", "url": "https://feverup.com/movies/en/united-states/movie-theaters/regal-cinemas-battery-park"},
    {"name": "Regal UA Sheepshead Bay", "address": "3907 Shore Pkwy, Brooklyn, NY 11235", "url": "https://feverup.com/movies/en/united-states/movie-theaters/regal-ua-sheepshead-bay"},
    {"name": "Regal UA Kaufman Astoria", "address": "35-30 38th St, Astoria, NY 11101", "url": "https://feverup.com/movies/en/united-states/movie-theaters/regal-ua-kaufman-astoria"}
]

def scrape_nyc_movie_showtimes():
    logger.info("Scheduler started: Scraping movie showtimes...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    all_showings = []

    for theater in theaters:
        theater_name = theater["name"]
        base_url = theater["url"]

        for i in range(7):  # Today + next 6 days
            date_obj = datetime.today() + timedelta(days=i)
            date_str = date_obj.strftime('%Y-%m-%d')

            if i == 0:
                url = base_url
            else:
                url = f"{base_url}?date={date_str}"

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            movie_blocks = soup.find_all('li', class_='showtime-list__item')

            for movie in movie_blocks:
                title_tag = movie.find('h3', class_='movie-card-info__title')
                if not title_tag:
                    continue
                title = title_tag.text.strip()

                format_blocks = movie.find_all('div', class_='movie-showtime-times')

                for format_block in format_blocks:
                    format_name_tag = format_block.find('p', class_='movie-showtime-times__title')
                    format_name = format_name_tag.text.strip() if format_name_tag else "Standard"

                    showtime_buttons = format_block.find_all('button', class_='showtimes-tile')
                    showtimes = [
                        btn.text.strip() for btn in showtime_buttons
                        if 'showtimes-tile--is-disabled' not in btn.get('class', [])
                    ]

                    if showtimes:
                        all_showings.append({
                            "theater": theater_name,
                            "movie": title,
                            "format": format_name,
                            "date": date_str,
                            "showtimes": showtimes
                        })

    output = {
        "scraped_date": datetime.today().strftime('%Y-%m-%d'),
        "showings": all_showings
    }

    with open(CACHE_FILE, 'w') as f:
        json.dump(output, f)

    logger.info("Scheduler completed: Scraping finished.")

    return output

def load_cached_data():
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Cache not found. Please trigger a refresh."}

@app.route('/showtimes', methods=['GET'])
def get_showtimes():
    data = load_cached_data()
    return jsonify(data)

@app.route('/theaters', methods=['GET'])
def get_theaters():
    return jsonify({"theaters": theaters})

@app.route('/refresh', methods=['GET'])
def manual_refresh():
    data = scrape_nyc_movie_showtimes()
    return jsonify({"status": "Refreshed", "data": data})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "NYC Movie Showtimes API is running."})

# Start the scheduler at 4:00 AM daily for production (or testing)
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_nyc_movie_showtimes, 'cron', hour=4, minute=0, misfire_grace_time=60 * 60 * 2)  # 2 hours grace time
    scheduler.start()

# Start the scheduler in a separate thread
if __name__ == '__main__':
    scheduler_thread = Thread(target=start_scheduler)
    scheduler_thread.start()

    # Start Flask
    scrape_nyc_movie_showtimes()  # Initial scrape for testing
    app.run(debug=True)
