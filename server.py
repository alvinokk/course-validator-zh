import http.server
import json
import urllib.request
import urllib.error
import os
from pathlib import Path

PORT = int(os.environ.get('PORT', 3000))
BASE_DIR = Path(__file__).parent

# Load API key: env var takes priority, then local .env file
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not API_KEY:
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith('ANTHROPIC_API_KEY='):
                API_KEY = line.split('=', 1)[1].strip().strip('"\'')
                break


class Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            content = (BASE_DIR / 'index.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('X-Frame-Options', 'ALLOWALL')
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path != '/api/validate':
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        body = json.loads(raw)
        payload = body.get('payload', {})

        # Accept key from request body (local use) or env var (production)
        key = body.get('apiKey', '') or API_KEY

        if not key:
            self._json(400, {'error': {'message': 'No API key. Set ANTHROPIC_API_KEY in .env file or enter it in the tool.'}})
            return

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=data,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': key,
                'anthropic-version': '2023-06-01',
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = resp.read()
            self._raw(200, result)
        except urllib.error.HTTPError as e:
            self._raw(e.code, e.read())
        except Exception as e:
            self._json(500, {'error': {'message': str(e)}})

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _raw(self, code, body):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == '__main__':
    if not API_KEY:
        print('WARNING: ANTHROPIC_API_KEY not set. Users must enter their key in the tool.')
    else:
        print(f'API key loaded (ends in ...{API_KEY[-6:]})')
    server = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'Course Validator running at http://localhost:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
