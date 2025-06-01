from http.server import BaseHTTPRequestHandler, HTTPServer
from settings import TEMP_HTTP_SRV_PORT


# HTTP-сервер с доступом только к preseed файлу
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/preseed.cfg":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(open("preseed.cfg", "rb").read())
        else:
            self.send_error(403)

    def log_message(self, format, *args):
        pass


httpd = HTTPServer(('', TEMP_HTTP_SRV_PORT), Handler)
httpd.serve_forever()
