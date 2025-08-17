from picamguard import create_app

app = create_app()

if __name__ == "__main__":
    # dev server; for prod run via systemd or a WSGI server
    app.run(host="0.0.0.0", port=5000)
