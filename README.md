# 🎬 NYC Movie Showtimes API

A lightweight Flask-based API that scrapes movie showtimes from AMC and Regal theaters in New York City via FeverUp.  
It provides easy-to-use endpoints to access current and upcoming movie screenings across multiple theaters.

---

## 🚀 Features
- Scrapes showtimes for **15+ NYC theaters** (AMC & Regal).
- Caches showtimes and auto-refreshes daily at **4:00 AM**.
- Provides clean JSON responses for easy integration (e.g., Bolt.new, dashboards, apps).
- Manual refresh and health check endpoints included.

---

## 📌 Endpoints

| Endpoint        | Method | Description                                |
|-----------------|--------|--------------------------------------------|
| `/showtimes`    | GET    | Returns cached showtimes for the current week |
| `/theaters`     | GET    | Lists all supported theaters with addresses and FeverUp URLs |
| `/refresh`      | GET    | Manually trigger a fresh scrape (updates cache) |
| `/health`       | GET    | Check API status                           |

---

## 🕒 Scheduler
This API uses **APScheduler** to automatically refresh movie showtimes every day at **4:00 AM**.

- The cache is stored locally in `cached_showtimes.json`.
- You can manually refresh by calling:
