import os

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG ={
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "qwerty"),
    "database": os.getenv("DB_NAME", "qarelecturev3db")
}


CHEMIN_PREPARATION = "/opt/....."


def get_db():
    # 1. Établir la connexion
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
   
    # 2. Configurer l'encodage sur l'objet connexion
    conn.set_client_encoding('UTF8')
   
    # 3. Retourner la connexion
    return conn