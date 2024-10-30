from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, text
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coffee_reviews.db'
app.config['UPLOAD_FOLDER'] = 'instance/uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB
db = SQLAlchemy(app)


# Current schema version
SCHEMA_VERSION = 2


class SchemaVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False)


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
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)


def get_db_version():
    version_record = SchemaVersion.query.first()
    if version_record is None:
        return 0
    return version_record.version


def set_db_version(version):
    version_record = SchemaVersion.query.first()
    if version_record is None:
        version_record = SchemaVersion(version=version)
        db.session.add(version_record)
    else:
        version_record.version = version
    db.session.commit()


def migrate_v1_to_v2():
    # Add the date column to the review table
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE review ADD COLUMN date DATETIME'))
        conn.commit()

    # Update existing reviews with a default date
    default_date = datetime.now(timezone.utc)
    reviews = Review.query.all()
    for review in reviews:
        review.date = default_date

    db.session.commit()
    print("Migration from v1 to v2 completed successfully!")


def run_migrations():
    with app.app_context():
        db.create_all()  # This will create the SchemaVersion table if it doesn't exist
        current_version = get_db_version()

        if current_version < 1:
            # Your database is at the initial state, no migrations needed
            set_db_version(1)

        if current_version < 2:
            migrate_v1_to_v2()
            set_db_version(2)

        # Add more migration steps here for future versions

        print(f"Database schema is now at version {SCHEMA_VERSION}")


@app.route('/')
def index():
    search = request.args.get('search', '')
    if search:
        coffee_beans = CoffeeBean.query.filter(
            CoffeeBean.name.contains(search)).all()
    else:
        coffee_beans = CoffeeBean.query.all()

    # Sort coffee beans by their average rating
    coffee_beans.sort(key=lambda x: x.average_rating, reverse=True)

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


@app.route('/delete_coffee/<int:id>', methods=['POST'])
def delete_coffee(id):
    coffee = CoffeeBean.query.get_or_404(id)
    if coffee.image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], coffee.image))
        except OSError:
            pass  # If the file doesn't exist, just ignore
    db.session.delete(coffee)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete_review/<int:coffee_id>/<int:review_id>', methods=['POST'])
def delete_review(coffee_id, review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    return redirect(url_for('coffee_detail', id=coffee_id))


if __name__ == '__main__':
    run_migrations()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
