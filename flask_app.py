from flask import Flask, redirect, render_template, request, url_for
import git

app = Flask(__name__)

comments = []

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", comments=comments)

    comments.append(request.form["contents"])
    return redirect(url_for('index'))
                        
@app.route('/commit', methods=["GET", "POST"])
def webhook():
    if request.method in ["GET", "POST"]:
        repo = git.Repo('/home/Grok/grok_online')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    return 'Wrong event type', 400
