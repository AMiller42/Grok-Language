from flask import Flask, render_template, request, url_for, flash, redirect
from flask_cors import CORS 
import multiprocessing, secrets
import PyGrok
import git
app = Flask(__name__)
CORS(app)

import os, sys, shutil

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__)) + "/.."
sys.path.insert(1, THIS_FOLDER)

shutil.rmtree("sessions", ignore_errors=True)
os.system("mkdir sessions")

sessions = {}
terminated = set()

@app.route('/', methods=['POST','GET'])
def index():
    session = secrets.token_hex(64)
    sessions[session] = None
    return render_template('main.html', session=session)


@app.route("/execute", methods=['POST'])
def execute():
    flags = request.form['flags']
    code = request.form['code'].replace("\r", "")
    input_list = request.form["inputs"].replace("\r", "")
    session = request.form["session"]

    if session not in sessions:
      return {"stdout": "", "stderr": "The session was invalid! You may need to reload your tab."}

    shutil.rmtree(f"sessions/{session}", ignore_errors=True)
    os.mkdir(f"sessions/{session}")

    with open(f"sessions/{session}/.stdin", "w", encoding="utf-8") as f:
      f.write(input_list)
    
    with open(f"sessions/{session}/.stdin", "r", encoding="utf-8") as x:
      with open(f"sessions/{session}/.stdout", "w", encoding="utf-8") as y:
        with open(f"sessions/{session}/.stderr", "w", encoding="utf-8") as z:
            manager = multiprocessing.Manager()
            ret = manager.dict()

            if "5" in flags:
                time = 5
            elif "f" in flags:
                time = 10
            elif "F" in flags:
                time = 15
            elif "b" in flags:
                time = 30
            elif "B" in flags:
                time = 120
            else:
                time = 60
            ret[1] = ""
            ret[2] = ""
            sessions[session] = multiprocessing.Process(target=PyGrok.execute, args=(code, flags, input_list, ret))
            sessions[session].start()
            sessions[session].join(time)
            
            if session in terminated:
                terminated.remove(session)
                ret[2] += "\nSession terminated upon user request"

            if sessions[session].is_alive():

                sessions[session].kill()
                if 2 in ret:
                    ret[2] += "\n" + f"Code timed out after {time} seconds"
            output = ret[1]
            y.write(ret[1])
            z.write(ret[2])
    with open(f"sessions/{session}/.stdout", "r", encoding="utf-8") as x:
        with open(f"sessions/{session}/.stderr", "r", encoding="utf-8") as y:
            val = {"stdout": x.read(), "stderr": y.read()}
    shutil.rmtree(f"sessions/{session}", ignore_errors=True)
    return val


@app.route("/kill", methods=['POST'])
def kill():
  session = request.form["session"]
  if sessions.get(session) is None: return ""
  sessions[session].kill()
  terminated.add(session)
  return ""


@app.route('/commit', methods=['POST'])
def webhook():
    if request.method in ["POST"]:
        repo = git.Repo('/home/Grok/grok_online')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    return 'Wrong event type', 400
