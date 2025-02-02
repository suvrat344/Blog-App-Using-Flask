from extensions import bcrypt, db, login_manager
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, current_user, logout_user
from forms import LoginForm, RegistrationForm
from models import User

auth_blueprint = Blueprint('auth',__name__)

@auth_blueprint.route("/register", methods = ["GET", "POST"])
def register():
  if current_user.is_authenticated:
    return redirect(url_for("home"))
  form = RegistrationForm()
  if(form.validate_on_submit()):
    username=form.username.data
    email = form.email.data
    hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
    user = User(username = username, email = email, password = hashed_password)
    db.session.add(user)
    db.session.commit()
    flash(f'Your account has been created! You are now able to log in.', category = "success")
    return redirect(url_for('auth.login'))
  return render_template("register.html", title = "Register", form = form)


@auth_blueprint.route("/login", methods = ["GET", "POST"])
def login():
  if current_user.is_authenticated:
    return redirect(url_for("home"))
  form = LoginForm()
  if(form.validate_on_submit()):
    user = User.query.filter_by(email = form.email.data).first()
    if(user and bcrypt.check_password_hash(user.password, form.password.data)):
      login_user(user, remember = form.remember.data)
      next_page = request.args.get('next')
      return redirect(next_page) if next_page else redirect(url_for('home'))
    else:
      flash("Login Unsuccessful. Please check email and password", category = 'danger')
  return render_template("login.html", title = "Login", form = form)


@auth_blueprint.route("/logout")
def logout():
  logout_user()
  return redirect(url_for('home'))
