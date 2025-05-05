from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
import os
import cv2
import base64
from io import BytesIO
from PIL import Image
from omr_logic import evaluate_omr  # Your OMR logic function

# Initialize the app and database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite DB file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# User class (database model)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registration form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=150)])
    submit = SubmitField('Sign Up')

# Login form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")  # Landing page with Login/Signup options

@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to dashboard after login
        else:
            flash('Login failed. Check your email and/or password', 'danger')
    return render_template('login.html', form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html')  # Show dashboard with options

@app.route("/view_scorecards")
@login_required
def view_scorecards():
    # Placeholder: Display scorecards or results history from the database
    return render_template('scorecards.html')  # Create this page later to show scorecards



@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have logged out successfully', 'success')
    return redirect(url_for('login'))

# Route for OMR page (upload or capture)

@app.route("/omr_evaluation", methods=["GET", "POST"])
@login_required
def process_omr_evaluation():
    score = None  # Initialize score to None
    if request.method == "POST":
        if 'omr' in request.files:  # Check if OMR file is uploaded
            file = request.files['omr']
            answer_string = request.form.get('answers', '')
            if file and answer_string:
                ans = list(map(int, answer_string.strip().split(',')))  # Parse correct answers
                filepath = os.path.join('static', 'upload.jpg')
                file.save(filepath)  # Save uploaded file

                # Process the OMR and evaluate the score
                final_img, score = evaluate_omr(filepath, ans)  # Pass both filepath and ans

                # Save the result image
                cv2.imwrite('static/result.jpg', final_img)

    # Return the OMR evaluation page with the score (if available)
    return render_template('evaluate_omr.html', score=score)



if __name__ == '__main__':
    app.run(debug=True)
