from flask import Flask, jsonify
from typing import Any
import random
from flask import request
from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db" # <- тут путь к БД

app = Flask(__name__)
# app.config('JSON_AS_ASCII') = False

"""
quotes = [
    {
        "id": 1,
        "author": "Albert Einstein",
        "text": "Logic will get you from A to B. Imagination will take you everywhere."
    },
    {
        "id": 2,
        "author": "Mahatma Gandhi",
        "text": "Be the change that you wish to see in the world."
    },
    {
        "id": 3,
        "author": "Oscar Wilde",
        "text": "Be yourself; everyone else is already taken."
    }

    ]
# Добавление рейтинга
for quote in quotes:
    if "rating" not in quote:
        quote["rating"] = 1
"""

# Исправления рейтинга на 1 (по умолчанию) при некорректных значениях
def check_rating(rating):
    if rating in ['1', '2', '3', '4', '5']:
        return rating
    return 1



# Задания 1 и 2
@app.route("/quotes/<int:id>")
def get_quote(id):
    
    for quote in quotes:
        if quote["id"] == id:
            return jsonify(quote), 200
    
    return {"error": f"Цитата № {id} не найдена"}, 404 # Возвращаем ошибку 404


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


# Add method POST - функцию оставляю для задачи с рейтингом, но внесу в нее некоторые изменения
@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    data['id'] = f"{quotes[-1]['id'] + 1}" # Нужно же добавить в словарик id новой цитаты

    try:
        data["rating"] = check_rating(data["rating"])
    except:
        data["rating"] = 1
    
    quotes.append(data)
    return jsonify(quotes), 201


# Add method DELETE
@app.route("/quotes/<int:id>", methods=['DELETE'])
def del_quote(id):
    for quote in quotes:
        if quote["id"] == id:
            quotes.remove(quote)
            return jsonify({'message': f'Цитата с id {id} уничтожена'}), 200
    return {"error": f"Цитата № {id} не найдена"}, 404 # Возвращаем ошибку 404


# Add method PUT - функцию оставляю для задачи с рейтингом, но внесу в нее некоторые изменения
@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    new_data = request.get_json()
    if not new_data:
        return {"error": "Отсутствуют данные"}, 400

    for quote in quotes:
        if quote["id"] == id:
            for key, value in new_data.items():
                if key in quote:
                    if key == 'rating':           # Для проверки изменений рейтинга
                        print(key, ' ', value)
                        quote[key] = check_rating(value)
                    else:
                        quote[key] = value
            return jsonify(quote), 200

    return {"error": f"Цитата с id {id} не найдена"}, 404


# Добавил фильтры. Сначала выбираем по автору, потом по рейтингу. Можно реализовать другим способом
@app.route("/quotes/filters", methods=["POST"])
def filter_quotes_by_json():
    data = request.get_json()

    filtered = quotes

    if "author" in data:
        author = data["author"]
        filtered = [q for q in filtered if q.get("author") == author]

    if "rating" in data:
        try:
            rating = int(data["rating"])
            if 1 <= rating <= 5:
                filtered = [q for q in filtered if q.get("rating") == rating]
            else:
                return {"Ошибка": "Рейтинг может быть от 1 до 5"}, 400
        except:
            return {"Ошибка": "Рейтинг может быть от 1 до 5"}, 400

    if (filtered) == []:
        return 'Цитат, соответствующих критериям поиска, не найдено', 201
    return jsonify(filtered), 201


if __name__ == "__main__":
    app.run(debug=True)