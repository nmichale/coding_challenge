from app.routes import app

# Keeping this the same for now, but would change to a production server (gunicorn etc.) in an actual app
app.run(debug=True)
