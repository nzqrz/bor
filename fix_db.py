import sqlite3

con = sqlite3.connect("data.db")
cur = con.cursor()

# Добавляем колонку worker_id
try:
    cur.execute("ALTER TABLE users ADD COLUMN worker_id INTEGER DEFAULT 0")
    con.commit()
    print("✅ Колонка worker_id добавлена")
except:
    print("⚠️ Колонка уже существует")

con.close()