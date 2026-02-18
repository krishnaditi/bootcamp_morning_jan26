from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Post

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aditi.db'
app.config['SECRET_KEY'] = 'Aditi23@'

db.init_app(app)

def create_admin():
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@example.com')
        db.session.add(admin_user)
        db.session.commit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        new_user = User(username=username, email=email)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        user = User.query.filter_by(username=username).first()
        if user:
            return redirect(url_for('user_dashboard', username=user.username))
    return render_template('login.html')

@app.route('/user_dashboard')
def user_dashboard():
    return render_template('user_dashboard.html')

with app.app_context():
    db.create_all()
    create_admin()

if __name__ == '__main__':
    app.run(debug=True)
