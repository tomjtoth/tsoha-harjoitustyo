from flask import send_from_directory, render_template, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, force_https
import users
import clinics
import donations
import consumables
import re
from datetime import date

# checking name lengths is taken care of here, too
re_names = re.compile(r"^(.{1,100}), *(.{1,100})$")

# this is not working as flask won't run on both http and https
# @app.before_request


def before_request():
    if force_https and not request.is_secure:
        return redirect(
            request.url.replace('http://', 'https://', 1),
            code=301
        )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html",
                               blood_types=users.all_blood_types)
    if request.method == "POST":
        password = request.form["password"]
        if password != request.form["pw-verify"]:
            return render_template("error.html", err="Salasanat eroavat")

        if len(password) < 8:
            return render_template("error.html", err="liian lyhyt salasana")

        names = re_names.match(request.form["names"])

        if not (names):
            return render_template("error.html", err="nimet väärin")

        if users.register(
            request.form["username"],
            password,
            names.group(2),
            names.group(1),
            users.flags_from_form(
                int(request.form["gender"]) == 1,
                int(request.form["blood-type"])
            )
        ):
            return redirect("/")
        else:
            return render_template(
                "error.html",
                operation='rekisteröinti',
                err="Käyttäjätunnus varmaan otettu jo")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if users.login(username, password):
            return redirect("/")
        else:
            return render_template(
                "error.html",
                operation='kirjautuminen',
                err="Väärä tunnus tai salasana")


@app.route("/logout")
def logout():
    del session["user"]
    return redirect("/")


@app.route('/')
def root():
    return render_template('index.html',
                           plots=[
                               donations.plot(),
                               donations.plot(crit="blood_type"),
                               donations.plot(session['user']['id']) if session.get(
                                   'user') else None
                           ])


@app.route('/donate', methods=["GET", "POST"])
def donate():
    if not session.get('user'):
        return redirect('/login')

    if request.method == "GET":
        return render_template('donation.html',
                               clinics=clinics.get_names(),
                               today=date.today(),
                               consumables=consumables.get_all())
    else:
        comment = request.form['comment']

        if len(comment) > 5000:
            return render_template("error.html", err="liian pitkä kommentti")

        if donations.register(
            request.form['date'],
            request.form['clinic'],
            request.form.getlist('consumption', int),
            comment
        ):
            return redirect('/')
        else:
            return render_template('error.html', err='emt')


@app.route('/comments')
def comments():
    return render_template('comments.html', comments=donations.all_comments())
