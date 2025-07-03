import sqlite3
import re
import ast

def create_sqlite_db():
    # Создаем или подключаем базу данных
    conn = sqlite3.connect('aromas.db')
    cursor = conn.cursor()
    
    # Создаем таблицу с SQLite-совместимым синтаксисом
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aromas (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        aroma TEXT,
        description TEXT,
        URL TEXT
    )
    """)
    
    # Читаем данные из output.txt
    with open('output.txt', 'r', encoding='utf-8') as f:
        data_lines = f.readlines()
    
    # Обрабатываем каждую строку с данными
    for line in data_lines:
        line = line.strip()
        if not line:
            continue
            
        try:
            # Безопасно преобразуем строку в кортеж с помощью ast.literal_eval
            data_tuple = ast.literal_eval(line)
            
            # Распаковываем кортеж при вставке
            cursor.execute("""
            INSERT INTO aromas (ID, brand, aroma, description, URL)
            VALUES (?, ?, ?, ?, ?)
            """, *data_tuple)  # Распаковка кортежа
            
        except (ValueError, SyntaxError, sqlite3.Error) as e:
            print(f"Ошибка при обработке строки: {line}")
            print(f"Ошибка: {e}")
            continue
    
    # Устанавливаем следующий ID (аналог AUTO_INCREMENT)
    cursor.execute("UPDATE sqlite_sequence SET seq = 1064 WHERE name = 'aromas'")
    
    conn.commit()
    conn.close()
    print("SQLite база данных 'aromas.db' успешно создана!")

if __name__ == "__main__":
    create_sqlite_db()