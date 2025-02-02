'''
Run flask app in windows
1. set FLASK_APP=app.py
2. flask run

Run flask app in linux/mac
1. export FLASK_APP=app.py
2. flask run

     OR
1. python app.py
'''
from auth import auth_blueprint
from extensions import bcrypt, db, login_manager, mail
from flask import abort, Flask, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from forms import PostForm, UpdateAccountForm
from models import Post, User
from PIL import Image
import os
import secrets


app = Flask(__name__)
app.config["SECRET_KEY"] = "ffa0fccc10f1316f42d253cc0516e3e7"
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///site.db'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')

bcrypt.init_app(app)
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
mail.init_app(app)

app.register_blueprint(auth_blueprint)


@app.route("/")
@app.route("/home")
def home():
  page = request.args.get('page', 1, type = int)
  posts = Post.query.order_by(Post.date_posted.desc()).paginate(page = page, per_page = 5)
  return render_template("home.html", posts = posts)


@app.route("/about")
def about():
  return render_template("about.html", title = "About")


def save_picture(form_picture):
  random_hex = secrets.token_hex(8)
  _, f_ext = os.path.splitext(form_picture.filename)
  picture_fn = random_hex + f_ext
  picture_path = os.path.join(app.root_path, 'static/images', picture_fn)
  output_size = (125, 125)
  i = Image.open(form_picture)
  i.thumbnail(output_size)
  i.save(picture_path)
  return picture_fn


@app.route("/account", methods = ["GET", "POST"])
@login_required
def account():
  form = UpdateAccountForm()
  if (form.validate_on_submit()):
    if(form.picture.data):
      picture_file = save_picture(form.picture.data)
      current_user.image_file = picture_file
    current_user.username = form.username.data
    current_user.email = form.email.data
    db.session.commit()
    flash("Your account has been updated!", category = "success")
    return redirect(url_for('account'))
  elif(request.method == "GET"):
    form.username.data = current_user.username
    form.email.data = current_user.email
  image_file = url_for('static', filename = 'images/' + current_user.image_file)
  return render_template("account.html", title = "Account", image_file = image_file , form = form)


@app.route("/post/new", methods = ["GET", "POST"])
@login_required
def new_post():
  form = PostForm()
  if(form.validate_on_submit()):
    post = Post(title = form.title.data, content = form.content.data, author = current_user)
    db.session.add(post)
    db.session.commit()
    flash("Your post has been created!", category = "success")
    return redirect(url_for('home'))
  return render_template("create_post.html", title = "New Post", form = form, legend = "New Post")


@app.route("/post/<int:post_id>", methods = ["GET", "POST"])
def post(post_id):
  post = Post.query.get_or_404(post_id)
  return render_template("post.html", title=post.title, post = post)


@app.route("/post/<int:post_id>/update", methods = ["GET", "POST"])
@login_required
def update_post(post_id):
  post = Post.query.get_or_404(post_id)
  if(post.author != current_user):
    abort(403)
  form = PostForm()
  if(form.validate_on_submit()):
    post.title = form.title.data
    post.content = form.content.data
    db.session.commit()
    flash("Your post has been updated!", category = "success")
    return redirect(url_for('post',post_id = post.id))
  elif(request.method == "GET"):  
    form.title.data = post.title
    form.content.data = post.content
  return render_template("create_post.html", title = "Update Post", form = form, legend = "Update Post")
  

@app.route("/post/<int:post_id>/delete", methods = ["POST"])
@login_required
def delete_post(post_id):
  post = Post.query.get_or_404(post_id)
  if(post.author != current_user):
    abort(403)
  db.session.delete(post)
  db.session.commit()
  flash("Your post has been deleted!", category = "success")
  return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_post(username):
  page = request.args.get('page', 1, type = int)
  user = User.query.filter_by(username = username).first_or_404()
  posts = Post.query.filter_by(author = user)\
    .order_by(Post.date_posted.desc())\
    .paginate(page = page, per_page = 5)
  return render_template("user_post.html", posts = posts, user = user)


if __name__ == "__main__":
  app.run(debug = True)