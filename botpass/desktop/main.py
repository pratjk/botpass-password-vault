import threading
import time
import webview
import sys

from botpass.web.app import app

def start_server():
    # Run Flask in a background thread
    # Werkzeug's reloader doesn't play nice with threads, so we disable it
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def main():
    print("Starting Botpass Core server...")
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    # Give the server a tiny bit of time to bind to the port
    time.sleep(1)
    
    print("Launching Desktop Window...")
    # Wrap the Flask app in a native OS window
    webview.create_window(
        title="🔐 Cryptokeep - Botpass",
        url="http://127.0.0.1:5000/login",
        width=900,
        height=700,
        min_size=(600, 500)
    )
    
    try:
        webview.start()
    except Exception as e:
        print(f"Error starting webview: {e}")
        print("\nFallback: You can open http://127.0.0.1:5000 in your regular browser.")
        # If webview fails, keep the main thread alive so Flask continues serving
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == '__main__':
    main()
