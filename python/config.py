import os

DB_CONFIG ={
    "host": os.getenv("DB_HOST", "10.10.10.24"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "qarelecturev3db")
}
