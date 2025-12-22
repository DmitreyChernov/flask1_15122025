from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from typing import Any
import random
from sqlalchemy import String
from werkzeug.exceptions import HTTPException
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pathlib import Path
from flask_migrate import Migrate


BASE_DIR = Path(__file__).parent
DB_NAME = "quotes.db"


class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(model_class=Base)
db.init_app(app)

migrate = Migrate(app, db)

class Quote(db.Model):
    __tablename__ = 'quotes' 

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author: Mapped[str] = mapped_column(String(100), nullable=False)  
    text: Mapped[str] = mapped_column(String(500), nullable=False)  
    rating: Mapped[int] = mapped_column(nullable=False, default=1)

    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author,
            "text": self.text,
            "rating": self.rating
        }


def check_rating(rating_value: Any, is_new: bool) -> int | None:
    try:
        rating = int(rating_value)
        if 1 <= rating <= 5:
            return rating
    except:
        return None


@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({"error": e.description}), e.code


# Локальный фронтенд
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/quotes", methods=["GET"])
def get_quotes():
    quotes = Quote.query.all()
    return jsonify([q.to_dict() for q in quotes])


@app.route("/quotes/<int:id>", methods=["GET"])
def get_quote(id):
    quote = Quote.query.get_or_404()
    return jsonify(quote.to_dict())


@app.route("/quotes/count", methods=["GET"])
def quotes_count():
    count = Quote.query.count()
    return jsonify({"count": count})


@app.route("/quotes/random", methods=["GET"])
def random_quote():
    quotes = Quote.query.all()
    if not quotes:
        return jsonify({"error": "Нет цитат"}), 404
    return jsonify(random.choice(quotes).to_dict())


@app.route("/quotes", methods=["POST"])
def create_quote():
    data = request.get_json()
    if not data or "author" not in data or "text" not in data:
        return jsonify({"error": "Требуются поля 'author' и 'text'"}), 400

    rating = check_rating(data.get("rating"), is_new=True) or 1
    new_quote = Quote(author=data["author"], text=data["text"], rating=rating)

    db.session.add(new_quote)
    try:
        db.session.commit()
        return jsonify(new_quote.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Ошибка при сохранении в БД"}), 500


@app.route("/quotes/<int:id>", methods=["PUT"])
def edit_quote(id):
    quote = Quote.query.get_or_404(id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Отсутствуют данные"}), 400

    updated = False
    if "author" in data:
        quote.author = str(data["author"]).strip()
        updated = True
    if "text" in data:
        quote.text = str(data["text"]).strip()
        updated = True
    if "rating" in data:
        validated = check_rating(data["rating"], is_new=False)
        if validated is not None:
            quote.rating = validated
            updated = True

    if not updated:
        return jsonify({"error": "Нет валидных полей для обновления"}), 400

    try:
        db.session.commit()
        return jsonify(quote.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Ошибка при обновлении"}), 500


@app.route("/quotes/<int:id>", methods=["DELETE"])
def del_quote(id):
    quote = Quote.query.get_or_404(id)
    db.session.delete(quote)
    try:
        db.session.commit()
        return jsonify({"message": "Цитата удалена"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Ошибка при удалении"}), 500


@app.route("/quotes/filters", methods=["GET"])
def filter_quotes():
    query = Quote.query

    if "id" in request.args:
        try:
            query = query.filter(Quote.id == int(request.args["id"]))
        except:
            return jsonify({"error": "Параметр 'id' должен быть целым числом"}), 400

    if "author" in request.args:
        query = query.filter(Quote.author == request.args["author"])

    if "text" in request.args:
        query = query.filter(Quote.text == request.args["text"])

    if "rating" in request.args:
        try:
            rating = int(request.args["rating"])
            if 1 <= rating <= 5:
                query = query.filter(Quote.rating == rating)
            else:
                return jsonify({"error": "Рейтинг должен быть от 1 до 5"}), 400
        except:
            return jsonify({"error": "Параметр 'rating' должен быть целым числом"}), 400

    results = query.all()
    if not results:
        return jsonify({
            "message": "Цитаты по заданным критериям не найдены",
            "filters_applied": {k: v for k, v in request.args.items()}
        }), 200

    return jsonify([q.to_dict() for q in results])



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True) # Это для запуска с фронтендом у себя же.