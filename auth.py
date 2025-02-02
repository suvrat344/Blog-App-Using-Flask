from extensions import bcrypt, db, mail
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, current_user, logout_user
from flask_mail import Message
from forms import LoginForm, RegistrationForm, RequestResetForm, ResetPassword
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
  print("In Login ****************************************************")
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


def send_reset_email(user):
  token = user.get_reset_token()
  msg = Message('Password Reset Request', sender = 'noreply@demo.com', recipients = [user.email])
  msg.body = f'''To reset ypur password, visit the following link:
{url_for('auth.reset_token', token = token, _external = True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
  mail.send(msg)

@auth_blueprint.route("/reset_password", methods = ["GET", "POST"])
def reset_request():
  if(current_user.is_authenticated):
    return redirect(url_for('home'))
  form = RequestResetForm()
  if(form.validate_on_submit()):
    user = User.query.filter_by(email = form.email.data).first()
    send_reset_email(user)
    flash("An email has been sent with instruction to reset your password.", category = 'info')
    return redirect(url_for('auth.login'))
  return render_template("reset_request.html", title = "Reset Password", form = form)


@auth_blueprint.route("/reset_password/<token>", methods = ["GET", "POST"])
def reset_token(token):
  if(current_user.is_authenticated):
    return redirect(url_for('home'))
  user = User.verify_reset_token()
  if(user is None):
    flash("That is an invalid or expired token", category = 'warning')
    return render_template(url_for('reset_request'))
  form = ResetPassword()
  if(form.validate_on_submit()):
    hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
    user.password = hashed_password
    db.session.commit()
    flash(f'Your password has been updated! You are now able to log in.', category = "success")
    return redirect(url_for('auth.login'))
  return render_template('reset_token.html', title = 'Reset Password', form = form)