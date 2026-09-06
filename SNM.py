from flask import Flask,render_template,request,session,url_for,redirect
from itsdangerous import URLSafeTimedSerializer,SignatureExpired,BadSignature
import bcrypt
import mysql.connector
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password ="root",
    database = "snm_db"
)
cursor = connection.cursor()
SNM = Flask(__name__)
SNM.secret_key ="SNM-secret-key"

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
    notes = cursor.fetchall()
    return render_template(
        "SNMnotes.html",
        notes = notes
    )
@SNM.route("/note/<int:note_id>")
def view_single_note(note_id):
    if 'user_id' not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    cursor.execute(
        """
        SELECT note_id, user_id, title, content, created_at, updated_at
        FROM notes
         WHERE note_id = %s AND user_id = %s
        """,
        (note_id,user_id)
    )
    note = cursor.fetchone()
    if not note:
        return "Note not found or unauthorized"
    return render_template(
        "SNMviewnote.html",
        note=note
    )
@SNM.route("/update-note/<int:note_id>",methods=["GET","POST"])
def update_note(note_id):
    if 'user_id'not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    cursor.execute(
        """
        SELECT note_id, user_id, title, content, created_at, updated_at
        FROM notes
        WHERE note_id = %s AND user_id = %s
        """,
        (note_id,user_id)
    )
    note = cursor.fetchone()
    if not note:
        return "Note not found or unauthorized"

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        if not title or not content:
            return "Title and content are required"

        cursor.execute(
            """
            UPDATE notes SET title = %s, content = %s, updated_at = CURRENT_TIMESTAMP
            WHERE note_id = %s AND user_id = %s
            """,
            (title, content, note_id, user_id)
        )
        connection.commit()
        return redirect(
            url_for(
                "view_single_note",
                note_id=note_id
            )
        )

    return render_template("SNMupdatenote.html", note=note)

@SNM.route("/delete-note/<int:note_id>",methods=["POST"])
def delete_note(note_id):
    if 'user_id' not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    cursor.execute(
        """
        DELETE FROM notes
        WHERE note_id = %s 
        AND user_id = %s
        """,
        (note_id,user_id)
        
    )
    connection.commit()
    return redirect(url_for('view_notes'))


@SNM.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    SNM.run(debug=True,port=9000)