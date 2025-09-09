from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float,desc,asc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

MOVIE_API_KEY=os.environ.get('MOVIE_API_KEY')
MOVIE_READ_ACCESS_TOKEN=os.environ.get('MOVIE_READ_ACCESS_TOKEN')
PASS=os.environ.get('PASS')
'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap5(app)

# CREATE DB


class Base(DeclarativeBase):
    pass

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db = SQLAlchemy(model_class=Base)
# initialize the app with the extension
db.init_app(app)

class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    title: Mapped[str] = mapped_column(String(50), unique=True,nullable=False)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float,nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()

new_movie = Movie(
    title="Phone Booth",
    year=2002,
    description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    rating=7.3,
    ranking=10,
    review="My favourite character was the caller.",
    img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
)

# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()

class EditForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')

class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')



@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(asc(Movie.rating)))
    movies = result.scalars()
    record_count = db.session.query(Movie.title).count()
    # # Use .scalars() to get the elements rather than entire rows from the database

    for movie in movies:
        movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == movie.id)).scalar()
        movie_to_update.ranking = record_count
        db.session.commit()
        record_count -= 1

    result = db.session.execute(db.select(Movie).order_by(asc(Movie.rating)))
    movies = result.scalars()
    return render_template("index.html",movie_list=movies)

@app.route('/edit/<movie_id>', methods=["GET","POST"])
def edit_movie(movie_id):
    movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    form = EditForm()
    if form.validate_on_submit():
        movie_to_update.rating = float(request.form["rating"])
        movie_to_update.review = request.form["review"]
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form,movie=movie_to_update)

@app.route('/add/', methods=["GET","POST"])
def add_movie():
    form = AddForm()
    if form.validate_on_submit():
        url = "https://api.themoviedb.org/3/search/movie"
        params = {"query": request.form["title"]}
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiYmIxZjVkNTMzZWQ1ZmU2NzM3MWZlMjZmNjc1NGJlOCIsInN1YiI6IjY2MTRiMjA2YTZhNGMxMDE4NmJlNWMzMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.xw96cDJqSjbYUsfkxqlrT9w6IeAQebXs5riRN1XS3hY"
        }
        response = requests.get(url, headers=headers, params=params)
        print(response.raise_for_status())
        print(response.json())
        return render_template('select.html', search_results=response.json())
    return render_template('add.html', form=form)

@app.route("/<movie_id>")
def delete(movie_id):
    movie_to_delete = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add_new_movie/<movie_id>")
def add_new_movie(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"language": "en-us"}
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiYmIxZjVkNTMzZWQ1ZmU2NzM3MWZlMjZmNjc1NGJlOCIsInN1YiI6IjY2MTRiMjA2YTZhNGMxMDE4NmJlNWMzMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.xw96cDJqSjbYUsfkxqlrT9w6IeAQebXs5riRN1XS3hY"
    }
    response = requests.get(url, headers=headers, params=params)
    print(response.raise_for_status())
    print(response.json())
    data = response.json()
    new_movie = Movie(
        title=data["original_title"],
        year=data["release_date"].split("-")[0],
        description=data["overview"],
        rating=0.0,
        ranking=1,
        review="",
        img_url=f"https://image.tmdb.org/t/p/w500{data["poster_path"]}"
    )
    db.session.add(new_movie)
    db.session.commit()
    movie_to_update = db.session.execute(db.select(Movie).where(Movie.title == data["original_title"])).scalar()
    return redirect(url_for('edit_movie',movie_id=movie_to_update.id, movie=movie_to_update))




if __name__ == '__main__':
    app.run(debug=True)
