from flask import Flask, render_template
from models import db, User, Post

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aditi.db'
app.config['SECRET_KEY'] = 'Aditi23@'

db.init_app(app)

@app.route('/')
def home():
    return render_template('home.html')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
