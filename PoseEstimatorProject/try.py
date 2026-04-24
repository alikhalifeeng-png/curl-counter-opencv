import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="curl_counter"
)
cursor = db.cursor()

cursor.execute("INSERT INTO sessions (duration, total_reps) VALUES (99, 99)")
db.commit()
print("Inserted successfully, ID:", cursor.lastrowid)

cursor.close()
db.close()