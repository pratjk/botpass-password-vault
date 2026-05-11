import threading
import time
import sys
import webbrowser
import subprocess

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
    
    url = "http://127.0.0.1:5000/login"
    
    try:
        import webview
        print("Launching Desktop Window via PyWebView...")
        webview.create_window(
            title="🔐 Cryptokeep - Botpass",
            url=url,
            width=900,
            height=700,
            min_size=(600, 500)
        )
        webview.start()
    except ImportError:
        print("\n[WARNING] PyWebView could not be imported (missing dependencies like pythonnet).")
        print("Fallback: Launching Microsoft Edge in App Mode (Native Window Feel)...")
        try:
            # Launch Edge as a chromeless window
            subprocess.Popen(f'start msedge --app="{url}"', shell=True)
        except Exception:
            print("Edge not found. Falling back to default browser.")
            webbrowser.open(url)
            
        # Keep the main thread alive so Flask continues serving
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
    except Exception as e:
        print(f"Error starting webview: {e}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == '__main__':
    main()
