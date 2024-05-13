from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

import pickle
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# ######################################################
# ######################################################
# ######################################################
# ######################################################
# ######################################################
# ######################################################
def Recommendations(gender, part_time_job, absence_days, extracurricular_activities,
                    weekly_self_study_hours, math_score, history_score, physics_score,
                    chemistry_score, biology_score, english_score, geography_score,
                    total_score,average_score):
    scaler = pickle.load(open("model/scaler.pkl", 'rb'))
    model = pickle.load(open("model/ourmodel.pkl", 'rb'))
    class_names = ['Lawyer', 'Doctor', 'Government Officer', 'Artist', 'Unknown',
                'Software Engineer', 'Teacher', 'Business Owner', 'Scientist',
                'Banker', 'Writer', 'Accountant', 'Designer',
                'Construction Engineer', 'Game Developer', 'Stock Investor',
                'Real Estate Developer']
    
    # Encode categorical variables
    gender_encoded = 1 if gender.lower() == 'female' else 0
    part_time_job_encoded = 1 if part_time_job else 0
    extracurricular_activities_encoded = 1 if extracurricular_activities else 0
    
    # Create feature array
    feature_array = np.array([[gender_encoded, part_time_job_encoded, absence_days, extracurricular_activities_encoded,
                               weekly_self_study_hours, math_score, history_score, physics_score,
                               chemistry_score, biology_score, english_score, geography_score,total_score,average_score]])
    
    # Scale features
    scaled_features = scaler.transform(feature_array)
    
    # Predict using the model
    probabilities = model.predict_proba(scaled_features)
    
    # Get top five predicted classes along with their probabilities
    top_classes_idx = np.argsort(-probabilities[0])[:4]
    top_classes_names_probs = [(class_names[idx], probabilities[0][idx]) for idx in top_classes_idx]
    
    return top_classes_names_probs


# ######################################################
# ######################################################
# ######################################################
# ######################################################
# ######################################################
# ######################################################
# ######################################################
# ######################################################

app = Flask(__name__)
# MySQL database setup
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="carrier_recommendations"
)
cursor = db.cursor()
cursor1 = db.cursor()

# Ensure the 'students' table exists
cursor.execute('''CREATE TABLE IF NOT EXISTS students
             (student_ID INT AUTO_INCREMENT PRIMARY KEY,
              student_name VARCHAR(50) NOT NULL,
              student_email VARCHAR(50) NOT NULL,
              student_password VARCHAR(50) NOT NULL,
              student_mobile VARCHAR(10) NOT NULL,
              student_gender VARCHAR(50) NOT NULL,
              student_recommendation VARCHAR(50) DEFAULT 'Not recommended yet')''')


@app.route('/')
def index():
    return render_template('start.html')
# # @app.route('/')
# # def index():
# #     return redirect(url_for('login'))
# @app.route('/start')
# def start():
#     return render_template('start.html')

# Redirect to the start route when the user logs out
@app.route('/student_logout/<int:user_id>')
def student_logout(user_id):
    # Redirect to the start route
    cursor.execute("UPDATE students SET status = false WHERE student_id = %s", (user_id,))
        # Commit the transaction to make the change persistent
    db.commit()
    return render_template('start.html')


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    mobile = request.form['mobile']
    gender = request.form['gender']

    cursor.execute("SELECT COUNT(*) AS email_count FROM students WHERE student_email = %s", (email,))
    count = cursor.fetchone()
    if count and count[0] > 0:
        message = "Email allready Exist."
        return render_template('register.html', message= message)



    # Insert new record into the 'students' table
    cursor.execute("INSERT INTO students (student_name, student_email, student_password, student_mobile, student_gender) VALUES (%s, %s, %s, %s, %s)",
                 (name, email, password, mobile, gender))
    
    db.commit()
    message = "Registered Succesfully."

    return render_template('register.html', message= message)

from flask import request, render_template, redirect, url_for

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form['email']
    password = request.form['password']

    # Check if email and password match a record in the 'students' table
    cursor.execute("SELECT * FROM students WHERE student_email=%s AND student_password=%s", (email, password))
    user = cursor.fetchone()

    if user:
        # Assuming you want to update the 'status' column to true
        cursor.execute("UPDATE students SET status = true WHERE student_email = %s", (email,))
        # Commit the transaction to make the change persistent
        db.commit()
        return redirect(url_for('home', user_id=user[0], user_name=user[1]))
    else:
        message = "Invalid Email or Password"
        return render_template('login.html', message=message)


@app.route('/home/<int:user_id>/<user_name>')
def home(user_id, user_name):
    cursor.execute("select status from  students WHERE student_id = %s", (user_id,))
    status = cursor.fetchone()
    if status[0]:
        return render_template('home.html', user_id=user_id, user_name=user_name)
    else:
        return render_template('start.html')


@app.route('/profile/<int:user_id>')
def profile(user_id):
    # Fetch user data from the database based on user ID
    cursor.execute("SELECT * FROM students WHERE student_ID=%s", (user_id,))
    user = cursor.fetchone()

    if user:
        # Render profile template with user data
        return render_template('profile.html', user=user)
    else:
        return "User not found"
    
@app.route('/fill_form/<int:user_id>/<user_name>')
def fill_form(user_id,user_name):
    # Check if the user has already taken the test
    cursor.execute("SELECT COUNT(student_id) FROM results WHERE student_id = %s", (user_id,))
    count = cursor.fetchone()
    # print(count)
    if count[0]> 0:
        # If the test has already been taken, display a message
        message = "Test is all ready Taken"
        return render_template('home.html', user_id=user_id, message=message,user_name=user_name)
    else:
        # If the test has not been taken, render the form for the user to fill out
        return render_template('fill_form.html', user_id=user_id, user_name=user_name)


@app.route('/store_values/<int:user_id>/<user_name>', methods=['POST'])
def store_values(user_id, user_name):
    
    if request.method == 'POST':
        # Retrieve form data
        student_id=user_id;  # Change this accordingly
        gender = request.form['gender']
        part_time_job = request.form['part_time_job']
        absence_days = request.form['absence_days']
        extracurricular_activities = request.form['extracurricular_activities']
        weekly_self_study_hours = request.form['weekly_self_study_hours']
        math_score = request.form['math_score']
        history_score = request.form['history_score']
        physics_score = request.form['physics_score']
        chemistry_score = request.form['chemistry_score']
        biology_score = request.form['biology_score']
        english_score = request.form['english_score']
        geography_score = request.form['geography_score']
        total_score = request.form['total_score']
        average_score = request.form['average_score']


        
        # Insert data into the database
        insert_query = "INSERT INTO results (student_id,gender, part_time_job, absence_days, extracurricular_activities, weekly_self_study_hours, math_score, history_score, physics_score, chemistry_score, biology_score, english_score, geography_score, total_score, average_score) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (student_id,gender, part_time_job, absence_days, extracurricular_activities, weekly_self_study_hours, math_score, history_score, physics_score, chemistry_score, biology_score, english_score, geography_score, total_score, average_score))
        db.commit()
        #########################################################
        #########################################################
        #########################################################
        #########################################################
        if part_time_job == "No":
            part_time_job=False
        else:
            part_time_job=True

        if extracurricular_activities=="No":
            extracurricular_activities=False
        else:
            extracurricular_activities=True

        final_recommendations = Recommendations(gender=gender,
                                        part_time_job=part_time_job,
                                        absence_days=absence_days,
                                        extracurricular_activities=extracurricular_activities,
                                        weekly_self_study_hours=weekly_self_study_hours,
                                        math_score=math_score,
                                        history_score=history_score,
                                        physics_score=physics_score,
                                        chemistry_score=chemistry_score,
                                        biology_score=biology_score,
                                        english_score=english_score,
                                        geography_score=geography_score,
                                        total_score=total_score,
                                        average_score=average_score)

        print("Top recommended studies with probabilities:")
        print("="*50)

        ans=[]
        for class_name in final_recommendations:
            ans.append(class_name[0])

        if "Unknown" in ans:
            ans.remove("Unknown")
        

        cursor.execute("UPDATE students SET student_recommendation = %s, recommendation_2 = %s, recommendation_3 = %s WHERE student_ID = %s",(ans[0], ans[1], ans[2], user_id))
        db.commit()
        #########################################################
        ############################################### ##########
        #########################################################
        #########################################################
        #########################################################

        # Redirect to some other page or return a response
        message = "Submission successful."
        return render_template('home.html', user_id=user_id, message=message, user_name=user_name)


@app.route('/update/<int:user_id>')
def update(user_id):
    # Fetch user data from the database based on user ID
    cursor.execute("SELECT * FROM students WHERE student_ID=%s", (user_id,))
    user = cursor.fetchone()

    if user:
        # Render profile template with user data
        return render_template('update.html', user=user,user_id=user_id)
    else:
        return "User not found"
    
# @app.route('/update_info/<int:user_id>')
# def update_info(user_id):
#     # Fetch user data from the database based on user ID
#     name = request.form['name']
#     mobile = request.form['mobile']
#     # Update user information in the database
#     cursor.execute("UPDATE students SET student_name=%s, student_mobile=%s WHERE student_ID=%s", (name, mobile, user_id))
#     db.commit()

#     user = cursor.fetchone()

#     if user:
#         # Render profile template with user data
#         return render_template('update.html', user=user)
#     else:
#         return "User not found"


from flask import request

@app.route('/update_info/<int:user_id>', methods=['POST'])
def update_info(user_id):
    # Fetch user data from the form
    name = request.form['name']
    mobile = request.form['mobile']
    # Update user information in the database
    cursor.execute("UPDATE students SET student_name=%s, student_mobile=%s WHERE student_ID=%s", (name, mobile, user_id))
    db.commit()

    cursor.execute("SELECT * FROM students WHERE student_ID=%s", (user_id,))
    user = cursor.fetchone()
    message = "Succesffully updated"
    if user:
        # Render profile template with user data
        return render_template('update.html', user=user, message= message)
    else:
        return render_template('update.html', user=user)

@app.route('/back/<int:user_id>/<user_name>')
def back(user_id, user_name):
    # Fetch user_id from the session or database
    # user_id = 1  # replace this with your actual method of getting the user_id
    # Redirect to the start route
    return render_template('home.html', user_id=user_id, user_name=user_name)



#######################################################################
#######################################################################

#######################################################################

#######################################################################

#######################################################################


#######################################################################
#######################################################################

#######################################################################

#######################################################################

#######################################################################


@app.route('/admin_login')
def admin_login():
    return render_template('admin_login.html')


@app.route('/admin_login', methods=['POST'])
def admin_login_post():
    email = request.form['email']
    password = request.form['password']

    # Check if email and password match a record in the 'students' table
    cursor.execute("SELECT * FROM admin WHERE admin_email=%s AND admin_password=%s", (email, password))
    user = cursor.fetchone()

    cursor1.execute("SELECT * FROM students")
    id = cursor1.fetchall() 
    if user:
        # Successful admin_login
        return render_template('admin_home.html', user_name=user[0],user_id=user[1],  id=id)
    else:
        message = "Inavlid Email or Password"
        return render_template('admin_login.html',message = message)

######################################################333


@app.route('/search_student', methods=['POST'])
def search_student():
    email = request.form['email']

    # Execute a database query to search for the student by email
    cursor.execute("SELECT * FROM students WHERE student_email=%s", (email,))
    student = cursor.fetchone()

    cursor1.execute("SELECT * FROM students")
    id = cursor1.fetchall() 

    # Check if the student exists and render the template accordingly
    if student:
        return render_template('admin_home.html', student=student, id=id)
    else:
        message = "Data does Not Exist"
        return render_template('admin_home.html' , message=message, id=id)


@app.route('/fetch_student', methods=['POST'])
def fetch_student():
    student_id = request.form['studentID']

    # Execute a database query to fetch the student details by ID
    cursor.execute("SELECT * FROM students WHERE student_ID=%s", (student_id,))
    student = cursor.fetchone()

    cursor1.execute("SELECT * FROM students")
    id = cursor1.fetchall() 
    
    # Check if the student exists and render the template accordingly
    if student:
        return render_template('admin_home.html', student=student,id=id)
    else:
        return "Student not found"



@app.route('/delete_student', methods=['POST'])
def delete_student():
    student_id = request.form['studentID']

    # Execute a database query to delete the student record by ID
    cursor.execute("DELETE FROM students WHERE student_ID=%s", (student_id,))
    db.commit()
    message = "Deletion successful."

    cursor1.execute("SELECT * FROM students")
    id = cursor1.fetchall() 

    return render_template('admin_home.html' , message=message, id=id)

if __name__ == '__main__':
    app.run(debug=True)
