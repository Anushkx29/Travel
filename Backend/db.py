import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",          # change if needed
        password="Anushkx_29", 
        database="travel_db"
    )
    return conn