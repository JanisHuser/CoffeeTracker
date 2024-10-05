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
    reviews = db.relationship('Review', backref='coffee_bean', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strength = db.Column(db.Integer, nullable=False)
    intensity = db.Column(db.Integer, nullable=False)
    decaf = db.Column(db.Boolean, default=False)
    user_name = db.Column(db.String(50), nullable=False)
    coffee_bean_id = db.Column(db.Integer, db.ForeignKey('coffee_bean.id'), nullable=False)

@app.route('/')
def index():
    search = request.args.get('search', '')
    if search:
        coffee_beans = CoffeeBean.query.filter(CoffeeBean.name.contains(search)).all()
    else:
        coffee_beans = CoffeeBean.query.all()
    return render_template('index.html', coffee_beans=coffee_beans)

@app.route('/add_coffee', methods=['GET', 'POST'])
def add_coffee():
    if request.method == 'POST':
        name = request.form['name']
        image = request.files['image']
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_coffee = CoffeeBean(name=name, image=filename)
        db.session.add(new_coffee)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_coffee.html')

@app.route('/coffee/<int:id>', methods=['GET', 'POST'])
def coffee_detail(id):
    coffee = CoffeeBean.query.get_or_404(id)
    if request.method == 'POST':
        strength = request.form['strength']
        intensity = request.form['intensity']
        decaf = 'decaf' in request.form
        user_name = request.form['user_name']
        new_review = Review(strength=strength, intensity=intensity, decaf=decaf, user_name=user_name, coffee_bean_id=coffee.id)
        db.session.add(new_review)
        db.session.commit()
        return redirect(url_for('coffee_detail', id=id))
    return render_template('coffee_detail.html', coffee=coffee)

def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialized.")

@app.before_first_request
def setup_app(app):
    print ("hello, settign up db")
    init_db()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)