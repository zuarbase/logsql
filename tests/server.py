import sys
from http.server import HTTPServer, BaseHTTPRequestHandler


class HTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)

        sys.stderr.write(body.decode("utf-8"))
        sys.stderr.flush()

        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)

    def log_request(self, code="-", size="-"):
        pass


if __name__ == "__main__":
    HTTPD = HTTPServer(("", 1363), HTTPRequestHandler)
    HTTPD.serve_forever()
