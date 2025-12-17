from flask import Flask, jsonify
from typing import Any
import random
from flask import request



app = Flask(__name__)


about_me = {
    "name": "Dmitrey",
    "surname": "Chernov",
    "email": "psevdotrotheus@gmail.com"
    }

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


@app.route("/")
def hello_world():
    return "Hello, World!", 200


@app.route("/about")
def about():
    return about_me, 200


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
    return jsonify(quotes), 200


# Add method POST
@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    data['id'] = f"{quotes[-1]['id'] + 1}" # Нужно же добавить в словарик id новой цитаты
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



if __name__ == "__main__":
    app.run(debug=True)