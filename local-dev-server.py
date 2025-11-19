#!/usr/bin/env python3
"""
Simple local development server for the dashboard.
Serves the HTML file and proxies API requests to production.
"""
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import urllib.request
import json

PORT = 3000
PRODUCTION_API = "https://api.soilreadings.com"

class DevHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve the dashboard HTML
        if self.path == '/' or self.path == '/dashboard.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open('app/static/readings.html', 'rb') as f:
                self.wfile.write(f.read())
            return

        # Proxy API requests to production
        if self.path.startswith('/v1/') or self.path.startswith('/api/'):
            try:
                url = f"{PRODUCTION_API}{self.path}"
                print(f"Proxying: {url}")
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req) as response:
                    self.send_response(response.status)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(response.read())
            except Exception as e:
                print(f"Proxy error: {e}")
                self.send_error(500, f"Proxy error: {e}")
            return

        # Default handler for other files
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

print(f"""
🚀 Local Development Server Running!

Dashboard: http://localhost:{PORT}/
API Proxy: Production data at {PRODUCTION_API}

Edit app/static/readings.html and refresh your browser to see changes instantly!

Press Ctrl+C to stop.
""")

with socketserver.TCPServer(("", PORT), DevHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
