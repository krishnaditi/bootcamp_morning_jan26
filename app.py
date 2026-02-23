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
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.status == 'accepted':
                return redirect(url_for('user_dashboard', username=user.username))
            else:
                return "Your account is not approved yet."
    return render_template('login.html')

@app.route('/user_dashboard')
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    user = User.query.all()
    return render_template('admin_dashboard.html', user=user)

@app.route('/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.status = 'accepted'
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        results = User.query.filter(User.username.contains(query)).all()
        return render_template('admin_dashboard.html', user=results)
    return render_template('admin_dashboard.html', user=User.query.all())

with app.app_context():
    db.create_all()
    create_admin()

if __name__ == '__main__':
    app.run(debug=True)
