from flask import Flask, jsonify
from typing import Any
import random
from flask import request
from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db" # <- тут путь к БД

app = Flask(__name__)


# Поиск цитаты в базе данных по id
@app.route("/quotes/<int:id>")
def get_quote(id):
    
    select_quotes = f"SELECT DISTINCT * from quotes WHERE id={id}" # Использовал DISTINCT для исключения возможных ошибок в bd с повторами
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()
    cursor.execute(select_quotes)   # get list[tuple]
    quote_in_db = cursor.fetchone()
    cursor.close()
    connection.close()

    if not quote_in_db:
        return {"error": f"Цитата № {id} не найдена"}, 404 # Возвращаем ошибку 404

    keys = ["id", "author", "text"]
    
    quote = dict(zip(keys, quote_in_db))

    return jsonify(quote), 200


# Задание 3
@app.route("/quotes/count")
def quotes_count():
    return {"count": len(quotes)}, 200


# Задание 4 - если правильно понял задачу. Если нет, то готов доработать
@app.route("/quotes/random")
def random_quote():
    return jsonify(random.choice(quotes)), 200


# URL: /quotes
@app.route("/quotes")
def get_quotes() -> list[dict[str, Any]]:
    select_quotes = "SELECT * from quotes"
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()
    cursor.execute(select_quotes)   # get list[tuple]
    quotes_db = cursor.fetchall()
    cursor.close()
    connection.close()

    keys = ["id", "author", "text"]
    quotes = []

    for quote_bd in quotes_db:
        quote = dict(zip(keys, quote_bd))
        quotes.append(quote)
        print(f'Очередная цитата: {quote}')

    return jsonify(quotes), 200


@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
  
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()
    
    try:
        query = "INSERT INTO quotes (author, text) VALUES (?, ?)"
        cursor.execute(query, (data['author'], data['text']))
        connection.commit()
    except Exception as e:
        return jsonify({'error': f'ошибка при записи в базу данных {e}'}), 408
    finally:
        cursor.close()
        connection.close()

    return jsonify({'message': 'Цитата добавлена в базу данных'}), 201


@app.route("/quotes/<int:id>", methods=['DELETE'])
def del_quote(id):
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM quotes WHERE id = ?", (id,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': f'Цитата с id={id} не найдена'}), 404
        
        connection.commit()
        return jsonify({'message': 'Цитата успешно удалена из базы данных'}), 200

    except sqlite3.Error as e:
        return jsonify({'error': f'Ошибка базы данных: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Внутренняя ошибка сервера: {str(e)}'}), 500
    
    finally:
        cursor.close()
        connection.close()


@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    new_data = request.get_json()
    if not new_data:
        return {"error": "Отсутствуют данные"}, 400

    # Поля, которые разрешается обновлять
    fields = {"author", "text"}
    fields_to_update = {k: v for k, v in new_data.items() if k in fields}

    if not fields_to_update:
        return {"error": "Нет разрешённых полей"}, 400

    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT * FROM quotes WHERE id = ?", (id,))
        if cursor.fetchone() is None:
            return jsonify({"error": f"Цитата с id={id} не найдена"}), 404

        params = ", ".join([f"{field} = ?" for field in fields_to_update])
        query = f"UPDATE quotes SET {params} WHERE id = ?"
        values = list(fields_to_update.values()) + [id]

        cursor.execute(query, values)
        connection.commit()

        return jsonify({"message": f"Обновлены поля {fields_to_update} цитаты с id={id}"}), 200

    except sqlite3.Error as e:
        return jsonify({"error": f"Ошибка базы данных: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Внутренняя ошибка: {e}"}), 500
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    app.run(debug=True)