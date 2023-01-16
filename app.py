#TODO: 

from flask import Flask, render_template, redirect, url_for, request, make_response, current_app, abort
from flask_table import Table, Col
from flask_socketio import SocketIO, emit
import random

# tcode = teacher code, teachers generate and share this code with students, and students use this code to join the class (also referred to as scode and skey during student login)
# key = master key, used to verify teacher (students shouldn't have this)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config.from_object(__name__)
socketio=SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html.j2')

@app.route('/teacher-login', methods=['GET', 'POST'])
def teacher_login():
    error = ""
    if request.method == 'POST':
        if request.form["key"] != session['rkey']:
            print("received invalid key: " + request.form["key"])
            error = "Invalid key, try again"
        else:
            resp = make_response(redirect(url_for('teacher_dashboard')))
            resp.set_cookie('key', str(request.form["key"]))
            return resp
    return render_template('teacher-login.html.j2', error=error)

@app.route('/teacher-dashboard')    
def teacher_dashboard():
    #gotta use a socket to live update data??
    if True: #teacher id verification
        try:
            tcode = request.cookies['tcode']
            print("tcode: " + tcode)
        except KeyError:
            print("no tcode found")
            tcode = None
    if 'key' not in request.cookies:
        return redirect(url_for('teacher_login'))
    if tcode not in session['TeacherCodes']: #don't look at this code, it's a mess
        print("tcode not in session")
        print(session['TeacherCodes'])
        key = request.cookies['key']
        if key != session['rkey']:
            return redirect(url_for('teacher_login'))
        #generate random 6 digits
        x = random.randint(100000, 999999)
        while x in session['TeacherCodes']:
            x = random.randint(100000, 999999)
        session['TeacherCodes'] += [str(x)]
        print(session['TeacherCodes'])
        tcodeGen = 1
        tcode = str(x)
    else:
        tcodeGen = 0
    rStudents = agrStudentsGivenCode(session['Students'], tcode, True)
    if rStudents != []:
        votes = countVotes(getVotesOfStudents(rStudents))
        items = rStudents
        table= StudentTable(items)
        if tcodeGen == 0:
            return render_template('teacher-dashboard.html.j2', TEACHER_CODE=tcode,TABLE_ELM=table.__html__(), VOTES=votes)
        else:
            resp = make_response(render_template('teacher-dashboard.html.j2', TEACHER_CODE=tcode,TABLE_ELM=table.__html__(), VOTES=votes))
            resp.set_cookie('tcode', str(tcode))
            return resp
    else:
        voteSub = {
            "good": 0,
            "neutral": 0,
            "bad": 0
        }
        if tcodeGen == 0:
            return render_template('teacher-dashboard.html.j2', TEACHER_CODE=tcode,TABLE_ELM="No students have joined yet", VOTES=voteSub)
        else:
            resp = make_response(render_template('teacher-dashboard.html.j2', TEACHER_CODE=tcode,TABLE_ELM="No students have joined yet", VOTES=voteSub))
            resp.set_cookie('tcode', str(tcode))
            return resp



@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    error = ""
    if request.method == 'POST':
        if request.form["scode"] not in session['TeacherCodes']:
            error = "Invalid teacher code, please try again"
        else:
            resp = make_response(redirect(url_for('student_dashboard')))
            resp.set_cookie('tcode', str(request.form["scode"]))
            return resp
    return render_template('student-login.html.j2', error=error)

@app.route('/student-dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if request.method == 'POST':
        if True: #student id verification
            try:
                student_id = request.cookies['student_id']
                print("student id found: " + student_id)
            except KeyError:
                print("no student id found")
                student_id = None
            if student_id not in session['StudentCodes']:
                return redirect(url_for('student_dashboard', error=('Invalid request (student id not in internal database)')))
        if True: #tcode verification
            try:
                tcode = request.cookies['tcode']
                print("tcode: " + tcode)
            except KeyError:
                print("no tcode found")
                tcode = None
            if tcode not in session['TeacherCodes']:
                return redirect(url_for('student_dashboard', error=('Invalid request (tcode not in internal database)')))
        curStudent = session["Students"][student_id]
        txtResponse = ""
        curVote = curStudent["vote"]
        if "username" in request.form:
            username = ''.join(filter(str.isalnum, request.form["username"]))
            curStudent["username"] = username
            txtResponse = "Username changed to " + username + " successfully."
        elif "change-vote-yes" in request.form:
            curVote = "yes"
            print("Vote changed to yes")
        elif "change-vote-neutral" in request.form:
            curVote = "neutral"
            print("Vote changed to neutral")
        elif "change-vote-no" in request.form:
            curVote = "no"
            print("Vote changed to no")
        else:
            abort(400, "Invalid request (form data key not recognized, form data below)\n " + str(request.form))
        curStudent["vote"] = curVote
        session["Students"][student_id] = curStudent
        #TODO: improve this
        return render_template('student-dashboard.html.j2', TXT_RESPONSE=txtResponse, VOTE=convertVote(session["Students"][student_id]["vote"]), STUDENT_ID=student_id, SNAME=session["Students"][student_id]["username"])
    else:
        if True: #make this collapsable, essentially this handles student code generation and verification
            try:
                tcode = request.cookies['tcode']
                print("tcode: " + tcode)
            except KeyError:
                print("no tcode found")
                tcode = None
            if tcode not in session['TeacherCodes']:
                return redirect(url_for('student_login'))
            try:
                student_id = request.cookies['student_id']
                print("student id found: " + student_id)
            except KeyError:
                print("no student id found")
                student_id = None
            if student_id not in session['StudentCodes']:
                print("id not in session")
                #generate random 4 digits, using y instead of x to avoid confusion with teacher code generation (4 digits vs 6 digits also to avoid confusion)
                y = random.randint(1000, 9999)
                while y in session['StudentCodes']:
                    y = random.randint(1000, 9999)
                session['StudentCodes'] += [str(y)]
                session['Students'][str(y)] = {
                        'username': 'PlaceholderName'+str(y),
                        'vote': 'neutral',
                        'tcode-origin': tcode
                    }
                resp = make_response(render_template('student-dashboard.html.j2', STUDENT_ID=y, SNAME=session["Students"][str(y)]["username"], VOTE=convertVote(session["Students"][str(y)]["vote"])))
                resp.set_cookie('student_id', str(y))
                print("set sid: "+str(y))
                return resp
        #do stuff here
        return render_template('student-dashboard.html.j2', STUDENT_ID=student_id,SNAME=session["Students"][student_id]["username"], VOTE=convertVote(session["Students"][student_id]["vote"]))

def convertVote(inputName):
    if inputName.lower() == "yes":
        return "Good"
    elif inputName.lower() == "neutral":
        return "Neutral"
    elif inputName.lower() == "no":
        return "Bad"
    else:
        return inputName
def agrStudentsGivenCode(students, tcode, fixvotes):
    #returns [{...}, {...}, ...] (an array of dictionaries)
    #because students is {x:{...}, y:{...}, ...}
    #dict format is [{id: x, username: y, vote: z}, {id: x, username: y, vote: z}, ...}]
    agrdStudents = []
    for sid, nesteddict in students.items():
        if nesteddict["tcode-origin"] == tcode:
            if fixvotes == True:
                newDict = {"sid": sid, "username": nesteddict["username"], "vote": convertVote(nesteddict["vote"])}
            else:
                newDict = {"sid": sid, "username": nesteddict["username"], "vote": nesteddict["vote"]}
            agrdStudents += [newDict]
    return agrdStudents
def getVotesOfStudents(relevantStudents):
    votes = []
    for student in relevantStudents:
        votes += [student["vote"]]
    return votes
def countVotes(arrOfVotes):
    good = 0
    neutral = 0
    bad = 0
    for vote in arrOfVotes:
        if vote == "Good":
            good += 1
        elif vote == "Neutral":
            neutral += 1
        elif vote == "Bad":
            bad += 1
    return {"good": good, "neutral": neutral, "bad": bad}

class StudentTable(Table):
    sid = Col('Student ID')
    username = Col('Name')
    vote = Col('Vote')
    border = True

class Session(object):
    def __init__(self):
        self.real = {
            'rkey': '123456',
            'TeacherCodes': ["000000"],
            'StudentCodes': ["0000"],
            'Students': {
                '0000': {
                    'username': 'PlaceholderName0000',
                    'vote': 'neutral',
                    'tcode-origin': '000000'
                },
                '9999': {
                    'username': 'PlaceholderName9999',
                    'vote': 'neutral',
                    'tcode-origin': '000000'
                }
            }
        }

badsession = Session()
session = badsession.real

if __name__ == '__main__':
    socketio.run(app, debug=True)