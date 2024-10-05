from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coffee_reviews.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)


class CoffeeBean(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    roast = db.Column(db.String(50))
    intensity = db.Column(db.String(50))
    acidity = db.Column(db.String(50))
    origin_countries = db.Column(db.String(200))
    notes = db.Column(db.String(200))
    reviews = db.relationship('Review', backref='coffee_bean', lazy=True)

    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        ratings = [review.rating for review in self.reviews]
        return round(sum(ratings) / len(ratings), 1)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    user_name = db.Column(db.String(50), nullable=False)
    coffee_bean_id = db.Column(db.Integer, db.ForeignKey(
        'coffee_bean.id'), nullable=False)


@app.route('/')
def index():
    search = request.args.get('search', '')
    if search:
        coffee_beans = CoffeeBean.query.filter(
            CoffeeBean.name.contains(search)).all()
    else:
        coffee_beans = CoffeeBean.query.all()
    return render_template('index.html', coffee_beans=coffee_beans)


@app.route('/add_coffee', methods=['GET', 'POST'])
def add_coffee():
    if request.method == 'POST':
        name = request.form['name']
        roast = request.form['roast_level']
        intensity = request.form['intensity']
        acidity = request.form['acidity']
        origin_countries = request.form['origins']
        notes = request.form['notes']
        image = request.files['image']

        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_coffee = CoffeeBean(
            name=name,
            roast=roast,
            intensity=intensity,
            acidity=acidity,
            origin_countries=origin_countries,
            notes=notes,
            image=filename
        )
        db.session.add(new_coffee)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_coffee.html')


@app.route('/coffee/<int:id>', methods=['GET', 'POST'])
def coffee_detail(id):
    coffee = CoffeeBean.query.get_or_404(id)
    if request.method == 'POST':
        user_name = request.form['user_name']
        rating = int(request.form['rating'])
        comment = request.form['comment']

        new_review = Review(user_name=user_name, rating=rating,
                            comment=comment, coffee_bean_id=coffee.id)
        db.session.add(new_review)
        db.session.commit()
        return redirect(url_for('coffee_detail', id=id))

    return render_template('coffee_detail.html', coffee=coffee)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
