import http.server
import socketserver
import webbrowser
import os
import sys

# Change to the directory containing the HTML file
os.chdir(r"c:\Users\Montg\Documents\Fresh nutrients\Chatbot")

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

Handler = MyHTTPRequestHandler

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving HTML files at http://localhost:{PORT}/")
        print(f"Open http://localhost:{PORT}/chat_test_interface.html in your browser")
        print("Press Ctrl+C to stop the server")
        
        # Try to open the browser automatically
        try:
            webbrowser.open(f'http://localhost:{PORT}/chat_test_interface.html')
        except:
            pass
            
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
    sys.exit(0)
except OSError as e:
    if e.errno == 10048:  # Port already in use
        print(f"Port {PORT} is already in use. Try a different port.")
    else:
        print(f"Error: {e}")
    sys.exit(1)
