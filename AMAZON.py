
# from flask import Flask,render_template,request,
# import mysql.connector
# connection = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password ="root",
#     database = "snm_db"
# )
# cursor = connection.cursor()
# AMAZON = Flask(__name__)
# @AMAZON.route('/')
# def home():
#     return "Welcom to Registration System"

# @AMAZON.route('/register',methods=['GET','POST'])
# def register():
#     if request.method == "POST":
#         name = request.form.get("name")
#         email = request.form.get("email")
#         mobile = request.form.get("mobile")
#         password = request.form.get("password")
#         confirmpassword = request.form.get("confirmpassword")


#         if not name or not email or not mobile or not password or not confirmpassword:
#             return "All fields are required."
#         if password != confirmpassword:
#             return "Passwords do not match!"
#         cursor.execute(
#         """
#         select * from users
#         where email = %s
#         """,
#            (email,)
#         )
#         Duplicate_mail = cursor.fetchone()
#         if Duplicate_mail:
#             return "Email already exists!"
#         cursor.execute(
#             """
#             insert into users(name,email,mobile,password,confirmpassword)
#             values(%s,%s,%s,%s,%s)
#             """,
#             (name,email,mobile,password,confirmpassword)
#         )
#         connection.commit()
#         return "Registration is Successful!"
#     return render_template("Aregister.html")

# if __name__ == "__main__":
#     AMAZON.run(debug=True,port=9000)