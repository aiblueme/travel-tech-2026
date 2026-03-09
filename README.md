# 2026 Travel Tech Comparison

19 portable laptops ranked by weight, battery life, and real-world travel value for Southeast Asia carry-on use.

## Live

https://travel-tech-2026.shellnode.lol

## Stack

- Single-file HTML/CSS/JS (vanilla, no frameworks)
- nginx:alpine container
- Ghost VPS / Docker
- SSL via SWAG + Cloudflare DNS

## Run Locally

Open `index.html` in a browser, or:

    docker build -t travel-tech-2026 .
    docker run -p 8080:80 travel-tech-2026

## Deploy

    docker context use ghost
    docker build -t travel-tech-2026 .
    docker run -d --name travel-tech-2026 \
      --network=swag_default \
      -p 9090:80 \
      --restart unless-stopped \
      travel-tech-2026

## Data Sources

Product specs hand-curated from manufacturer pages. Images scraped via `scraper.py` (icrawler/Bing), converted to WebP, stored in `images/`.
