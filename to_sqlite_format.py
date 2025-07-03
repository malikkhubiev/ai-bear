import sqlite3
import re

# Исходный SQL текст
sql_text = """-- phpMyAdmin SQL Dump
-- version 5.0.2
-- https://www.phpmyadmin.net/
--
-- Хост: localhost
-- Время создания: Июн 26 2025 г., 00:29
-- Версия сервера: 5.7.44-48
-- Версия PHP: 7.4.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `u1723242_default`
--

-- --------------------------------------------------------

--
-- Структура таблицы `aromas`
--

CREATE TABLE `aromas` (
  `ID` bigint(20) UNSIGNED NOT NULL,
  `brand` varchar(128) DEFAULT NULL,
  `aroma` varchar(128) DEFAULT NULL,
  `description` varchar(1024) CHARACTER SET utf8mb4 DEFAULT NULL,
  `URL` varchar(256) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Дамп данных таблицы `aromas`
--

INSERT INTO `aromas` (`ID`, `brand`, `aroma`, `description`, `URL`) VALUES
(444, 'Abdul Samad Al Qurashi', 'Safari Extreme', '® Бренд: Abdul Samad Al Qurashi\r\n🇸🇦 Саудовская Аравия \r\n🥀 Пол: Унисекс\r\n\r\n🍃 Ноты: дерево уд, цветочные аккорды, ваниль, сандал, древесные аккорды, пряности ', 'https://bahur.store/o/4e7994/'),
(445, 'Abdul Samad Al Qurashi', 'Safari Extreme 2', 'Another description', 'https://example.com');

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `aromas`
--
ALTER TABLE `aromas`
  ADD PRIMARY KEY (`ID`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `aromas`
--
ALTER TABLE `aromas`
  MODIFY `ID` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1065;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
"""

def convert_mysql_to_sqlite(sql_text):
    # Удаляем MySQL специфичные выражения
    sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.DOTALL)
    sql_text = re.sub(r'--.*?\n', '\n', sql_text)
    sql_text = re.sub(r'SET.*?\n', '', sql_text)
    sql_text = re.sub(r'ENGINE=.*?;', ';', sql_text)
    sql_text = re.sub(r'CHARACTER SET \w+', '', sql_text)
    sql_text = re.sub(r'COMMIT;', '', sql_text)
    sql_text = re.sub(r'START TRANSACTION;', '', sql_text)
    
    # Заменяем MySQL типы данных на SQLite совместимые
    sql_text = sql_text.replace('bigint(20) UNSIGNED', 'INTEGER')
    sql_text = sql_text.replace('varchar', 'TEXT')
    sql_text = sql_text.replace('AUTO_INCREMENT', 'AUTOINCREMENT')
    
    # Удаляем UNSIGNED
    sql_text = sql_text.replace('UNSIGNED', '')
    
    # Удаляем ALTER TABLE для PRIMARY KEY (будем добавлять в CREATE TABLE)
    sql_text = re.sub(r'ALTER TABLE `aromas`\s+ADD PRIMARY KEY \(`ID`\);', '', sql_text)
    
    # Добавляем PRIMARY KEY в CREATE TABLE
    sql_text = re.sub(
        r'CREATE TABLE `aromas`\s*\((.*?)\);',
        r'CREATE TABLE IF NOT EXISTS aromas (\1, PRIMARY KEY (ID));',
        sql_text,
        flags=re.DOTALL
    )
    
    # Удаляем MODIFY для AUTO_INCREMENT
    sql_text = re.sub(
        r'ALTER TABLE `aromas`\s+MODIFY `ID`.*?AUTO_INCREMENT.*?;',
        '',
        sql_text,
        flags=re.DOTALL
    )
    
    # Удаляем лишние точки
    sql_text = sql_text.replace('...', '')
    
    return sql_text.strip()

# Преобразуем SQL
converted_sql = convert_mysql_to_sqlite(sql_text)

# Создаем SQLite базу данных
DB_FILE = 'bahur_bot.db'

conn = sqlite3.connect(DB_FILE)
try:
    conn.executescript(converted_sql)
    print(f'База данных {DB_FILE} успешно создана!')
    
    # Проверяем, что данные загрузились
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM aromas")
    count = cursor.fetchone()[0]
    print(f'Загружено {count} записей в таблицу aromas')
    
except Exception as e:
    print(f'Ошибка при импорте: {e}')
finally:
    conn.close()