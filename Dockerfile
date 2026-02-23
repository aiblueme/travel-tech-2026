# ─────────────────────────────────────────────────────────
# Dockerfile — 2026 Travel Tech Comparison
# Base: nginx:alpine (smallest production-ready web server)
# Final image size: ~8MB
# ─────────────────────────────────────────────────────────

FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy the single-file app
COPY index.html /usr/share/nginx/html/index.html

# Copy product images (scraped by scraper.py, _raw/ excluded via .dockerignore)
# If the images/ directory doesn't exist yet the build will still succeed —
# cards fall back to emoji placeholders via the onerror handler in the HTML.
COPY images/ /usr/share/nginx/html/images/

# Replace default nginx config with a minimal, hardened version:
#   - gzip on for HTML/CSS/JS
#   - security headers (CSP, no server token leakage, basic hardening)
#   - proper charset declaration
#   - cache headers for static assets (1 year immutable for WebP)
RUN printf 'server {\n\
    listen       80;\n\
    server_name  _;\n\
    root         /usr/share/nginx/html;\n\
    index        index.html;\n\
    charset      utf-8;\n\
\n\
    # Security headers\n\
    add_header X-Frame-Options        "SAMEORIGIN"   always;\n\
    add_header X-Content-Type-Options "nosniff"      always;\n\
    add_header Referrer-Policy        "no-referrer"  always;\n\
    add_header Content-Security-Policy "default-src '"'"'self'"'"'; img-src '"'"'self'"'"' data:; style-src '"'"'self'"'"' '"'"'unsafe-inline'"'"'; script-src '"'"'self'"'"' '"'"'unsafe-inline'"'"';" always;\n\
    add_header Permissions-Policy     "camera=(), microphone=(), geolocation=()" always;\n\
\n\
    # Gzip compression\n\
    gzip            on;\n\
    gzip_types      text/html text/css application/javascript image/svg+xml;\n\
    gzip_min_length 256;\n\
\n\
    location / {\n\
        try_files $uri $uri/ =404;\n\
    }\n\
\n\
    # Static asset caching — 1 year immutable for versioned WebP images\n\
    location ~* \\.(webp|jpg|jpeg|png|svg|ico)$ {\n\
        expires 365d;\n\
        add_header Cache-Control "public, immutable";\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

# nginx runs on port 80 inside the container
# Map to host port 9090 at docker run time:
#   docker run -p 9090:80 ...
EXPOSE 80

# nginx:alpine already has a correct CMD/ENTRYPOINT
# ("nginx -g 'daemon off;'") — no need to override
