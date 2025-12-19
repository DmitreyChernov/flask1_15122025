from flask import Flask, jsonify, request, g
from typing import Any
import random
from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db" # <- тут путь к БД

app = Flask(__name__)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(path_to_db)
    return db


@app.teardown_appcontext
def close_connection(exeption):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close


# Проверяем правильность рейтинга при новой записи или при изменении. 
# В засисимости от этого либо оставляем текущий рейтинг, либо вносим единицу 
# в качестве default значения.
def check_rating(rating_value: Any, is_new: bool) -> int | None:
    try:
        rating = int(rating_value)
        if 1 <= rating <= 5:
            return rating
    except:
        pass
    if is_new:
        return 1
    else:
        return None
    

# Поиск цитаты в базе данных по id
@app.route("/quotes/<int:id>")
def get_quote(id):
    # Использовал DISTINCT для исключения возможных ошибок в bd с повторами
    select_quotes = f"SELECT DISTINCT * from quotes WHERE id={id}"
    cursor = get_db().cursor()
    cursor.execute(select_quotes)
    quote_in_db = cursor.fetchone()
    if not quote_in_db:
        return {"error": f"Цитата № {id} не найдена"}, 404 # Возвращаем ошибку 404
    keys = ["id", "author", "text", "rating"]
    quote = dict(zip(keys, quote_in_db))
    return jsonify(quote), 200


@app.route("/quotes/count")
def quotes_count():
    try:
        cursor = get_db().cursor()
        quiry = "SELECT * FROM quotes"
        cursor.execute(quiry)
        num_quotes = len(cursor.fetchall())
        return jsonify({'message': f'Количество цитат в базе данных = {num_quotes}'}), 200
    except Exception as e:
        return jsonify({'error': 'Ошибка при подсчете количества цитат в базе данных: {e}'}), 404


@app.route("/quotes/random")
def random_quote():
    try:
        cursor = get_db().cursor()
        quiry = "SELECT * FROM quotes"
        cursor.execute(quiry)
        quotes = cursor.fetchall()
        return jsonify({'message': f'Случайная цитата: {random.choice(quotes)}'}), 200
    except Exception as e:
        return jsonify({'error': 'Ошибка при выборе случайной цитаты: {e}'}), 404


# URL: /quotes
@app.route("/quotes")
def get_quotes() -> list[dict[str, Any]]:
    select_quotes = "SELECT * from quotes"
    cursor = get_db().cursor()
    cursor.execute(select_quotes)
    quotes_db = cursor.fetchall()
    keys = ["id", "author", "text", "rating"]
    quotes = []
    for quote_bd in quotes_db:
        quote = dict(zip(keys, quote_bd))
        quotes.append(quote)
    return jsonify(quotes), 200


@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    if not data or "author" not in data or "text" not in data:
        return {"error": "Требуются поля 'author' и 'text'"}, 400

    rating = check_rating(data.get("rating"), is_new=True)

    connection = get_db()
    cursor = connection.cursor()

    try:
        query = "INSERT INTO quotes (author, text, rating) VALUES (?, ?, ?)"
        cursor.execute(query, (data['author'], data['text'], rating))
        last_id = cursor.lastrowid
        connection.commit()
        return jsonify({'message': f'Цитата добавлена с id={last_id}'}), 201

    except Exception as e:
        return jsonify({'error': f'Ошибка при записи: {e}'}), 500


@app.route("/quotes/<int:id>", methods=['DELETE'])
def del_quote(id):
    connection = get_db()
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


@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    new_data = request.get_json()
    if not new_data:
        return {"error": "Отсутствуют данные"}, 400

    connection = get_db()
    cursor = connection.cursor()

    try:
        # Проверяем, существует ли цитата
        cursor.execute("SELECT rating FROM quotes WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row is None:
            return jsonify({"error": f"Цитата с id={id} не найдена"}), 404
        current_rating = row[0]
        # Формируем данные для обновления
        update_fields = {}
        if "author" in new_data:
            update_fields["author"] = new_data["author"]
        if "text" in new_data:
            update_fields["text"] = new_data["text"]
        if "rating" in new_data:
            validated_rating = check_rating(new_data["rating"], is_new=False)
            if validated_rating is not None:
                update_fields["rating"] = validated_rating
        if not update_fields:
            return jsonify({"error": "Нет валидных полей для обновления"}), 400
        set_clause = ", ".join([f"{field} = ?" for field in update_fields])
        query = f"UPDATE quotes SET {set_clause} WHERE id = ?"
        values = list(update_fields.values()) + [id]
        cursor.execute(query, values)
        connection.commit()
        return jsonify({"message": f"Цитата с id={id} обновлена"}), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Ошибка БД: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Ошибка: {e}"}), 500


@app.route("/quotes/filters")
def filter_quotes():

    keys = ["id", "author", "rating", "text"] # Список разрешенных для фильтра параметров

    get_params = request.get_json()

    filters = {}

    for k in keys:

        match k:
            case "id":
                if get_params.get(k) is not None:
                    try:
                        filters["id"] = int(get_params.get(k))
                    except:
                        return jsonify({"error": "Параметр 'id' должен быть целым числом"}), 400
            case "author":
                if get_params.get(k) is not None:
                    filters["author"] = get_params.get(k)
            case "rating":
                if get_params.get(k) is not None:
                    try:
                        rating = int(get_params.get(k))
                        if 1 <= rating <= 5:
                            filters["rating"] = rating
                        else:
                            return jsonify({"error": "Параметр 'rating' должен быть от 1 до 5"}), 400
                    except:
                        return jsonify({"error": "Параметр 'rating' должен быть целым числом"}), 400
            case "text":
                if get_params.get(k) is not None:
                    filters["text"] = get_params.get(k)


    if not filters:
        return jsonify({"error": "Укажите хотя бы один фильтр: id, author, rating или text"}), 400

    try:
        connection = get_db()
        cursor = connection.cursor()
        keys_quiry = []
        values = []
        for field, value in filters.items():
            keys_quiry.append(f"{field} = ?")
            values.append(value)
        query = f"SELECT * FROM quotes WHERE {' AND '.join(keys_quiry)}"

        cursor.execute(query, values)
        result = cursor.fetchall()

        if not result:
            return jsonify({
                "message": "Нет цитат, соответствующих заданным критериям",
                "filters": {k: v for k, v in request.args.items()}
            }), 200
        
        quotes = [dict(zip(keys, row)) for row in result]
        return jsonify(quotes), 200
    except Exception as e:
        return jsonify({"error": f"Ошибка при работе с базой данных: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True)