from flask import Flask, render_template, request, redirect, jsonify, session
from db.adminhelper import getrecord, getall
from db.dbhelper import addrecord, updaterecord, deleterecord, getprocess
import qrcode
import os
from datetime import datetime

app = Flask(__name__)

IMAGE_FOLDER = "static/images"
QRCODE_FOLDER = "static/qrcode"

os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(QRCODE_FOLDER, exist_ok=True)

app.secret_key = "helloworld"
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

def admin_login_required():
    if not session.get("admin_logged_in"):
        return redirect("/login")


@app.route("/")
def index():
    return render_template("index.html", page="index", header_button={"text": "LOGIN", "href": "/login"})

@app.route("/scan")
def scan():
    idno = request.args.get("idno", "").strip()

    if not idno:
        return jsonify(found=False, message="Invalid QR")

    student = getrecord("students", idno=idno)

    if not student:
        return jsonify(found=False, message="Student not found")

    now = datetime.now()
    date_today = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")

    existing = getrecord(
        "attendance",
        student_id=idno,
        date=date_today
    )

    if existing:
        return jsonify(found=True, already=True)

    addrecord(
        "attendance",
        student_id=idno,
        time_in=time_now,
        date=date_today
    )

    return jsonify(found=True, already=False, idno=idno)


@app.route("/studview")
def studview():
    idno = request.args.get("idno", "").strip()
    found_param = request.args.get("found", "true")

    student = getrecord("students", idno=idno)

    if found_param == "false" or not student:
        fake_student = {
            "idno": "NO RECORD",
            "lastname": "NO RECORD",
            "firstname": "NO RECORD",
            "course": "NO RECORD",
            "level": "NO RECORD",
            "image": None,
            "qrcode": None
        }

        return render_template("studview.html", student=fake_student, found=False)

    return render_template("studview.html", student=student[0], found=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        admin = getrecord("admin", email=email, password=password)

        if len(admin) > 0:
            session["admin_logged_in"] = True  
            return redirect("/usermgt")
        else:
            error = "Invalid email or password"

    return render_template(
        "login.html",
        page="login",
        error=error,
        header_button={"text": "BACK", "href": "/"}
    )


@app.route("/usermgt")
def usermgt():
    if not session.get("admin_logged_in"):    
        return redirect("/login")

    admins = getall("admin")
    return render_template("usermgt.html", admins=admins)


@app.route("/studentmgt")
def studentmgt():
    if not session.get("admin_logged_in"):    
        return redirect("/login")

    students = getall("students")
    return render_template("studentmgt.html", students=students)


@app.route("/addstudent", methods=["GET", "POST"])
def addstudent():
    if not session.get("admin_logged_in"):     
        return redirect("/login")

    if request.method == "GET":
        return render_template(
            "addstudent.html",
            duplicate_idno=False,
            header_button={"text": "BACK", "href": "/studentmgt"}
        )

    idno = request.form.get("idno", "").strip()
    lastname = request.form.get("lastname", "").strip()
    firstname = request.form.get("firstname", "").strip()
    course = request.form.get("course", "").strip()
    level = request.form.get("level", "").strip()
    image_file = request.files.get("image_file")

    from db.adminhelper import getrecord
    existing = getrecord("students", idno=idno)

    if existing:
        return render_template(
            "addstudent.html",
            duplicate_idno=True,
            header_button={"text": "BACK", "href": "/studentmgt"}
        )

    if not (idno and lastname and firstname and course and level and image_file):
        return "Missing fields", 400

    filename = f"{idno}.png"

    img_path = os.path.join("static/images", filename)
    image_file.save(img_path)

    qr_path = os.path.join(QRCODE_FOLDER, filename)
    qr_img = qrcode.make(idno)
    qr_img.save(qr_path)

    addrecord(
        "students",
        idno=idno,
        lastname=lastname,
        firstname=firstname,
        course=course,
        level=level,
        image=filename,
        qrcode=filename
    )


    return redirect("/studentmgt")

@app.route("/updatestudent", methods=["GET", "POST"])
def updatestudent():
    if not session.get("admin_logged_in"):     
        return redirect("/login")

    if request.method == "GET":
        idno = request.args.get("id", "").strip()
        student = getrecord("students", idno=idno)

        if not student:
            return redirect("/studentmgt")

        return render_template(
            "updstudent.html",
            student=student[0],
            header_button={"text": "BACK", "href": "/studentmgt"}
        )

    idno = request.form.get("idno").strip()
    lastname = request.form.get("lastname").strip()
    firstname = request.form.get("firstname").strip()
    course = request.form.get("course").strip()
    level = request.form.get("level").strip()
    image_file = request.files.get("image_file")

    student = getrecord("students", idno=idno)[0]  

    if image_file and image_file.filename != "":
        filename = f"{idno}.png"
        image_file.save(os.path.join("static/images", filename))
    else:
        filename = student["image"]  

    updaterecord(
        "students",
        idno=idno,
        lastname=lastname,
        firstname=firstname,
        course=course,
        level=level,
        image=filename,
        qrcode=student["qrcode"]
    )


    return redirect("/studentmgt")

@app.route("/viewattendance")
def viewattendance():
    if not session.get("admin_logged_in"):    
        return redirect("/login")

    date = request.args.get("date", None)
    attendance_data = []

    if date:
        sql = """
        SELECT a.id, s.idno, s.lastname, s.firstname, s.course, s.level,
               a.time_in
        FROM attendance a
        JOIN students s ON a.student_id = s.idno
        WHERE a.date = ?
        ORDER BY a.time_in ASC
        """
        attendance_data = getprocess(sql, [date])

    return render_template(
        "viewattendance.html",
        header_button=None,
        attendance=attendance_data
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/login") 
    
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/addadmin", methods=["POST"])
def addadmin():
    if not session.get("admin_logged_in"):
        return jsonify(success=False, message="Unauthorized")

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    if not name or not email or not password:
        return jsonify(success=False, message="Missing fields")

    addrecord(
        "admin",
        name=name,
        email=email,
        password=password
    )

    admin = getrecord("admin", email=email)[0]

    return jsonify(
        success=True,
        message="Admin saved successfully",
        admin={
            "id": admin["id"],
            "name": admin["name"],
            "email": admin["email"],
            "password": admin["password"]
        }
    )

@app.route("/updateadmin", methods=["POST"])
def updateadmin():
    if not session.get("admin_logged_in"):
        return jsonify(success=False, message="Unauthorized")

    admin_id = request.form.get("id")
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    if not admin_id or not name or not email or not password:
        return jsonify(success=False, message="Missing fields")

    updaterecord(
        "admin",
        id=admin_id,
        name=name,
        email=email,
        password=password
    )

    admin = getrecord("admin", id=admin_id)[0]

    return jsonify(
        success=True,
        message="Admin updated successfully",
        admin={
            "id": admin["id"],
            "name": admin["name"],
            "email": admin["email"],
            "password": admin["password"]
        }
    )

@app.route("/deleteadmin", methods=["POST"])
def deleteadmin():
    if not session.get("admin_logged_in"):
        return jsonify(success=False, message="Unauthorized")

    admin_id = request.form.get("id")
    if not admin_id:
        return jsonify(success=False, message="Missing admin ID")

    deleterecord("admin", id=admin_id)
    return jsonify(success=True, message="Admin deleted successfully")

@app.route("/deletestudent", methods=["POST"])
def deletestudent():
    if not session.get("admin_logged_in"):
        return jsonify(success=False, message="Unauthorized")

    idno = request.form.get("idno")
    if not idno:
        return jsonify(success=False, message="Missing student ID")

    deleterecord("students", idno=idno)
    return jsonify(success=True, message="Student deleted successfully")

if __name__ == "__main__":
    app.run(debug=True)
