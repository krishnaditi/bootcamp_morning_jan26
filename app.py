from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from models import db, User, Post
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aditi.db'
app.config['SECRET_KEY'] = 'Aditi23@'

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'resumes')
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)

def create_admin():
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@example.com')
        admin_user.set_password('admin123')  # Set a default admin password
        db.session.add(admin_user)
        db.session.commit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/download_resume/<int:user_id>')
def download_resume(user_id):
    user = User.query.get(user_id)
    if user and user.resume_filename:
        return send_from_directory(app.config['UPLOAD_FOLDER'], user.resume_filename, as_attachment=True)
    flash('Resume not found.', 'danger')
    return redirect(url_for('home'))

@app.route('/view_resume/<int:user_id>')
def view_resume(user_id):
    user = User.query.get(user_id)
    if user and user.resume_filename:
        return send_from_directory(app.config['UPLOAD_FOLDER'], user.resume_filename)
    flash('Resume not found.', 'danger')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        # Check password length
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html')
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('register.html')
        
        # Handle resume upload
        resume_filename = None
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    # Create unique filename with username
                    filename = secure_filename(f"{username}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    resume_filename = filename
                else:
                    flash('Only PDF files are allowed for resume.', 'danger')
                    return render_template('register.html')
        
        # Create new user with hashed password
        new_user = User(username=username, email=email, resume_filename=resume_filename)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form['login_type']
        username = request.form['username']
        password = request.form['password']
        
        # Validate login type selection
        if not login_type:
            flash('Please select a login type.', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Invalid username. User not found.', 'danger')
            return render_template('login.html')
        
        # Check password
        if not user.check_password(password):
            flash('Invalid password. Please try again.', 'danger')
            return render_template('login.html')
        
        # Handle Admin Login
        if login_type == 'admin':
            if username == 'admin':
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('You are not authorized to login as admin.', 'danger')
                return render_template('login.html')
        
        # Handle User Login
        elif login_type == 'user':
            if username == 'admin':
                flash('Admin cannot login as user. Please select Admin login type.', 'warning')
                return render_template('login.html')
            elif user.status == 'accepted':
                flash('Login successful!', 'success')
                return redirect(url_for('user_dashboard', username=user.username))
            elif user.status == 'closed':
                flash('Your account has been closed. Contact admin to reactivate.', 'warning')
                return render_template('login.html')
            else:
                flash('Your account is not approved yet. Please wait for admin approval.', 'warning')
                return render_template('login.html')
    
    return render_template('login.html')

@app.route('/user_dashboard')
@app.route('/user_dashboard/<username>')
def user_dashboard(username=None):
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            posts = Post.query.filter_by(user_id=user.id).all()
            return render_template('user_dashboard.html', user=user, posts=posts)
    return redirect(url_for('login'))

@app.route('/view_post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get(post_id)
    if post:
        return render_template('view_post.html', post=post)
    flash('Post not found.', 'danger')
    return redirect(url_for('home'))

@app.route('/create_post/<int:user_id>', methods=['GET', 'POST'])
def create_post(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return render_template('create_post.html', user=user)
        
        new_post = Post(title=title, content=content, user_id=user_id)
        db.session.add(new_post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('user_dashboard', username=user.username))
    
    return render_template('create_post.html', user=user)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get(post.user_id)
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return render_template('edit_post.html', post=post, user=user)
        
        post.title = title
        post.content = content
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('user_dashboard', username=user.username))
    
    return render_template('edit_post.html', post=post, user=user)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post:
        user = User.query.get(post.user_id)
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully!', 'success')
        return redirect(url_for('user_dashboard', username=user.username))
    flash('Post not found.', 'danger')
    return redirect(url_for('home'))

@app.route('/close_post/<int:post_id>', methods=['POST'])
def close_post(post_id):
    post = Post.query.get(post_id)
    if post:
        user = User.query.get(post.user_id)
        post.status = 'closed'
        db.session.commit()
        flash('Post closed successfully! It will no longer be visible to others.', 'info')
        return redirect(url_for('user_dashboard', username=user.username))
    flash('Post not found.', 'danger')
    return redirect(url_for('home'))

@app.route('/reopen_post/<int:post_id>', methods=['POST'])
def reopen_post(post_id):
    post = Post.query.get(post_id)
    if post:
        user = User.query.get(post.user_id)
        post.status = 'active'
        db.session.commit()
        flash('Post reopened successfully!', 'success')
        return redirect(url_for('user_dashboard', username=user.username))
    flash('Post not found.', 'danger')
    return redirect(url_for('home'))

@app.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']
        
        # Check if username already exists (excluding current user)
        existing_user = User.query.filter(User.username == new_username, User.id != user_id).first()
        if existing_user:
            flash('Username already taken.', 'danger')
            return render_template('edit.html', user=user)
        
        # Check if email already exists (excluding current user)
        existing_email = User.query.filter(User.email == new_email, User.id != user_id).first()
        if existing_email:
            flash('Email already in use.', 'danger')
            return render_template('edit.html', user=user)
        
        user.username = new_username
        user.email = new_email
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_dashboard', username=user.username))
    
    return render_template('edit.html', user=user)

@app.route('/delete_profile/<int:user_id>', methods=['POST'])
def delete_profile(user_id):
    user = User.query.get(user_id)
    if user:
        # Delete associated posts first
        Post.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        flash('Your account has been deleted successfully.', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('home'))

@app.route('/close_profile/<int:user_id>', methods=['POST'])
def close_profile(user_id):
    user = User.query.get(user_id)
    if user:
        user.status = 'closed'
        db.session.commit()
        flash('Your profile has been closed. Contact admin to reactivate.', 'info')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('home'))

@app.route('/admin_dashboard')
def admin_dashboard():
    users = User.query.all()
    total_users = len(users)
    accepted_users = User.query.filter_by(status='accepted').count()
    pending_users = User.query.filter_by(status='rejected').count()
    rejected_users = User.query.filter_by(status='closed').count()
    
    return render_template('admin_dashboard.html', 
                           users=users,
                           total_users=total_users,
                           accepted_users=accepted_users,
                           pending_users=pending_users,
                           rejected_users=rejected_users,
                           search_query='',
                           status_filter='all')

@app.route('/admin_search', methods=['POST'])
def admin_search():
    query = request.form.get('query', '')
    status_filter = request.form.get('status_filter', 'all')
    
    # Build the query
    users_query = User.query
    
    # Filter by search query
    if query:
        users_query = users_query.filter(
            (User.username.contains(query)) | (User.email.contains(query))
        )
    
    # Filter by status
    if status_filter != 'all':
        users_query = users_query.filter_by(status=status_filter)
    
    users = users_query.all()
    
    # Get statistics
    total_users = User.query.count()
    accepted_users = User.query.filter_by(status='accepted').count()
    pending_users = User.query.filter_by(status='rejected').count()
    rejected_users = User.query.filter_by(status='closed').count()
    
    return render_template('admin_dashboard.html',
                           users=users,
                           total_users=total_users,
                           accepted_users=accepted_users,
                           pending_users=pending_users,
                           rejected_users=rejected_users,
                           search_query=query,
                           status_filter=status_filter)

@app.route('/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.status = 'accepted'
        db.session.commit()
        flash(f'User {user.username} has been approved.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/reject_user/<int:user_id>', methods=['POST'])
def reject_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.status = 'rejected'
        db.session.commit()
        flash(f'User {user.username} has been rejected.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route('/reactivate_user/<int:user_id>', methods=['POST'])
def reactivate_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.status = 'accepted'
        db.session.commit()
        flash(f'User {user.username} has been reactivated.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    user = User.query.get(user_id)
    if user and user.username != 'admin':
        Post.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

with app.app_context():
    db.create_all()
    create_admin()

if __name__ == '__main__':
    app.run(debug=True)
