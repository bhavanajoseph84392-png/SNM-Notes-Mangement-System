from flask import Flask,render_template,request,session,url_for,redirect
from itsdangerous import URLSafeTimedSerializer,SignatureExpired,BadSignature
import bcrypt
import mysql.connector
import os
from werkzeug.utils import secure_filename
from flask import send_file 
import flask_excel  

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password ="root",
    database = "snm_db"
)
cursor = connection.cursor()
SNM = Flask(__name__)
SNM.secret_key ="SNM-secret-key"
flask_excel.init_excel(SNM)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf","txt","docx","jpg","jpeg","png"}
SNM.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(SNM.config["UPLOAD_FOLDER"],exist_ok=True)
def allowed_file(filename): 
    return(
        "." in filename
        and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS
    )

def generate_reset_token(email): 
    serializer = URLSafeTimedSerializer(
        SNM.config['SECRET_KEY']
    )
    token = serializer.dumps(email,salt="password-reset")
    return token 

def verify_reset_token(token):
    serializer = URLSafeTimedSerializer(
        SNM.config['SECRET_KEY']
    )
    try:
        email = serializer.loads(
            token,salt="password-reset",max_age=300
        )
        return email
    except SignatureExpired:
        return "expired"
    except BadSignature:
        return "invalid"
    

@SNM.route('/')
def home():
    return "Welcom to Registration System"

@SNM.route('/register',methods=['GET','POST'])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            return "All fields are required."
        cursor.execute(
        """
        select * from users
        where email = %s
        """,
           (email,)
        )
        Duplicate_mail = cursor.fetchone()
        if Duplicate_mail:
            return "Email already exists!"

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        )

        hashed_password=hashed_password.decode("utf-8")

        cursor.execute(
            """
            insert into users(name,email,password)
            values(%s,%s,%s)
            """,
            (name,email,hashed_password)
        )
        connection.commit()
        return "Registration is Successful!"
    return render_template("SNMregister.html")

@SNM.route('/login',methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Email and password are required"

        cursor.execute(
            """
select * from users
where email = %s
""",
(email,)
        )
        user = cursor.fetchone()

        if not user:
            return"Invalid email or password"

        stored_password = user[3]
        if isinstance(stored_password,str):
            stored_password = stored_password.encode("utf-8")
        if bcrypt.checkpw(
            password.encode("utf-8"),
            stored_password
        ):  
            session["user_id"] = user[0]            
            session["email"] = user[2]   
            return redirect(url_for("dashboard"))
        return "Invalid email or password" 
    return render_template("SNMlogin.html")      

@SNM.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("SNMdashboard.html")  

@SNM.route("/forgot-password",methods=["GET","POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form.get("email")
        if not email:
            return "Email is required"

        cursor.execute(
            """
        select * from users
        where email = %s
            """,
            (email,)
        )
        user = cursor.fetchone()
        if not user:
            return "Email not registered"

        token = generate_reset_token(email)

        reset_link = url_for(
            "reset_password",
            token = token,
            _external=True
        )
        print(reset_link)
        return "Password reset link generated"
    return render_template("SNMforgotpassword.html")

@SNM.route("/reset-password/<token>",methods=["GET","POST"])
def reset_password(token):
    email = verify_reset_token(token)

    if email == "expired":
        return"Reset link has expired"

    if email == "invalid":
        return"Invalid reset link"

    if request.method == "POST":
        new_password = request.form.get("password")
        if not new_password:
            return "Password is required"

        hashed_password = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            """
            UPDATE users SET password = %s WHERE email = %s
            """,
            (hashed_password,email)
        )
        connection.commit()
        return "Password reset successful"
    return render_template("SNMresetpassword.html")

@SNM.route('/add-note',methods=["GET","POST"])
def add_note():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")


        if not title or not content:
            return "Title and content are required"

        user_id=session["user_id"]


        cursor.execute(
            """
            INSERT INTO notes
            (user_id, title, content)
            VALUES(%s, %s, %s)
            """,
            (user_id, title, content)
        )
        connection.commit()
        return redirect(url_for("view_notes"))
    return render_template("SNMaddnote.html")

@SNM.route('/notes')
def view_notes():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    cursor.execute(
        """
        SELECT note_id, user_id, title, content, created_at, updated_at
        FROM notes WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )        
    user_note = cursor.fetchall()
    return render_template(
        "SNMnotes.html",
        user_note = user_note
    )

@SNM.route('/notes/<int:note_id>')
def view_single_note(note_id):
    if 'user_id' not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    cursor.execute(
        """SELECT note_id, user_id,title,content,created_at,updated_at
        FROM notes
        WHERE note_id = %s AND user_id = %s
        """,
        (note_id, user_id)
    )
    note = cursor.fetchone()

    if not note:
        return "NOte not found or unauthorized"

    return render_template(
        "SNMviewnote.html",
        note = note
    )
@SNM.route("/update-note/<int:note_id>",methods=["GET","POST"])
def update_note(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cursor.execute(
        """
        SELECT note_id, user_id,title,content,created_at,updated_at
        FROM notes
        WHERE note_id = %s AND user_id = %s
        """,
            (note_id, user_id)
    )
    note = cursor.fetchone()
    
    if not note:
        return "NOte not found or unauthorized"

    if request.method == "POST":
            title = request.form.get("title")
            content = request.form.get("content")

            if not title or not content:
                return "Title and content are required"
            cursor.execute(
                """UPDATE notes
                   SET title = %s,
                    content = %s
                    WHERE note_id = %s
                    AND user_id = %s
                """,
                    (title, content, note_id, user_id)
            )
            connection.commit()
            return redirect(url_for("view_single_note",
                note_id = note_id
                )
            )
    return render_template(
        "SNMupdatenote.html",
        note=note
    )


@SNM.route("/delete-note/<int:note_id>", methods=["POST"])
def delete_note(note_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor.execute(
        """
        DELETE FROM notes
        WHERE note_id = %s
        AND user_id = %s
        """,
        (note_id, user_id)
    )

    connection.commit()

    return redirect(url_for("view_notes"))

@SNM.route("/upload-file/<int:note_id>",methods=['GET','POST'])

def upload_file(note_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cursor.execute(
        """
        SELECT note_id
        FROM notes
        WHERE note_id = %s AND user_id = %s""",
        (note_id, user_id)
    )
    note = cursor.fetchone()

    if not note:
        return "Note not found or unauthorized" 

    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            return "No file uploaded"

        if file.filename == "":
            return "No file selected"

        if not allowed_file(file.filename):
            return "File type not allowed"

        filename = secure_filename(file.filename)

        cursor.execute(
            """SELECT file_id
            FROM filedata
            WHERE note_id = %s AND file_name = %s""",
            (note_id, filename)
        )

        existing_file = cursor.fetchone()

        if existing_file:
            return "This file is already uploaded for this note"

        filepath = os.path.join(
            SNM.config["UPLOAD_FOLDER"],
            filename
        )
        file.save(filepath)

        cursor .execute(
            """INSERT INTO filedata
            (note_id,  file_name,file_path)
            VALUES (%s,%s,%s)""",
            (note_id, filename, filepath)
        )

        connection.commit()

        return "File uploaded successfully"

    return render_template(
        "SNMuploadfile.html",
        note_id = note_id
    )

@SNM.route("/files")
def view_all_files():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cursor.execute(
        """SELECT filedata.file_id,
        filedata.note_id,
        filedata.file_name,
        filedata.file_path,
        filedata.uploaded_at,
        notes.title
        FROM filedata
        JOIN notes
        ON filedata.note_id = notes.note_id
        WHERE notes.user_id = %s
        ORDER BY filedata.uploaded_at DESC
        """,
        (user_id,)
    )
    files = cursor.fetchall()

    return render_template(
        "SNMfiles.html", 
        files=files
    )



@SNM.route("/view-file/<int:file_id>")
def view_file(file_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor.execute(
        """SELECT filedata.file_path
           FROM filedata
           JOIN notes
           ON filedata.note_id = notes.note_id
           WHERE filedata.file_id = %s
           AND notes.user_id = %s
        """,
        (file_id, user_id)
    )

    file = cursor.fetchone()

    if not file:
        return "File not found or unauthorized"

    return send_file(
        file[0],
        as_attachment=False
    )

@SNM.route("/download-file/<int:file_id>")
def download_file(file_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor.execute(
        """SELECT filedata.file_path,
                  filedata.file_name
           FROM filedata
           JOIN notes
           ON filedata.note_id = notes.note_id
           WHERE filedata.file_id = %s
           AND notes.user_id = %s
        """,
        (file_id, user_id)
    )

    file = cursor.fetchone()

    if not file:
        return "File not found or unauthorized"

    return send_file(
        file[0],
        as_attachment=True,
        download_name=file[1]
    )  
@SNM.route("/delete-file/<int:file_id>", methods=["POST"])
def delete_file(file_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor.execute(
        """SELECT filedata.file_path,
                  filedata.note_id
           FROM filedata
           JOIN notes
           ON filedata.note_id = notes.note_id
           WHERE filedata.file_id = %s
           AND notes.user_id = %s
        """,
        (file_id, user_id)
    )

    file = cursor.fetchone()

    if not file:
        return "File not found or unauthorized"

    file_path = file[0]
    note_id = file[1]

    if os.path.exists(file_path):
        os.remove(file_path)

    cursor.execute(
        """DELETE FROM filedata
           WHERE file_id = %s
        """,
        (file_id,)
    )

    connection.commit()

    return redirect(
        url_for("view_single_note", note_id=note_id)
    )

@SNM.route("/search",methods=["GET","POST"])
def search():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # notes = []
    # files = []

    if request.method == "POST":
        search_text = request.form.get("search","").strip()

        if not search_text:
            return "Please enter search text"

        user_id = session["user_id"]
        search_value = "%" + search_text + "%"
        cursor.execute(
            """SELECT note_id,title,content, created_at
            FROM notes
            WHERE user_id = %s
            AND (title LIKE %s OR content LIKE %s)""",
            (user_id, search_value, search_value)
        )
        notes = cursor.fetchall()

        cursor.execute(
            """SELECT filedata.file_id,
                    filedata.note_id,
                    filedata.file_name,
                    filedata.file_path,
                    filedata.uploaded_at
                    FROM filedata
                    JOIN notes
                    ON filedata.note_id = notes.note_id
                    WHERE notes.user_id = %s
                    AND filedata.file_name LIKE %s
                    """,
                    (user_id, search_value)
        )
        files = cursor.fetchall()

    return render_template(
            "SNMsearch.html",
                        notes=notes,
                        files=files
    )

@SNM.route("/download-note-files-excel/<int:note_id>")
def download_note_files_excel(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cursor.execute(
        """SELECT note_id, title
        FROM notes
        WHERE note_id = %s
        AND user_id =%s""",
        (note_id, user_id)

    )
    note = cursor.fetchone()

    if not note:
        return "Note not found"

    cursor.execute(
        """SELECT file_id,file_name,file_path, uploaded_at
        FROM filedata
        WHERE note_id =%s""",
        (note_id,)
    )
    files = cursor.fetchall()

    data = [
        ["File ID","File Name", "File Path", "Uploaded At"]
    ]

    for file in files:
        data.append(list(file))

        return flask_excel.make_response_from_array(
            data,
            file_type="xlsx",
            file_name=f"{note[1]}_files.xlsx"
        )
     
@SNM.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    SNM.run(debug=True,port=9000)