import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Mode debug hanya menyala kalau FLASK_ENV=development di .env (jangan pernah di server publik)
    app.run(debug=os.getenv("FLASK_ENV") == "development", port=5000)
