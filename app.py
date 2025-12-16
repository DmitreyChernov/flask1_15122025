from flask import Flask
import random

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
    return "Hello, World!"


@app.route("/about")
def about():
    return about_me


# Задания 1 и 2
@app.route("/quotes/<int:id>")
def get_quote(id):
    
    for quote in quotes:
        if quote["id"] == id:
            return quote
    
    return {"error": f"Цитата № {id} не найдена"}, 404 # Возвращаем ошибку 404


# Задание 3
@app.route("/quotes/count")
def quotes_count():
    return {"count": len(quotes)}


# Задание 4 - если правильно понял задачу. Если нет, то готов доработать
@app.route("/quotes/random")
def random_quote():
    return random.choice(quotes)


if __name__ == "__main__":
    app.run(debug=True)