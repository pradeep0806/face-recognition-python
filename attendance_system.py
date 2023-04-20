import cv2
import face_recognition
import os
import numpy as np
from datetime import datetime, timedelta
import mysql.connector

# Constants
PATH = "RESOURCES"
WAIT_TIME = 30 # In minutes

# Load images and names
imgs = []
image_files = os.listdir(PATH)
images = []
persons_names=[]

# images are loaded and their names are stored
for img_file in image_files:
    img= cv2.imread(f"{PATH}/{img_file}")
    images.append(img)
    persons_name = img_file.split(".")[0]
    persons_names.append(persons_name)

# Function to mark attendance in the database
def mark_attendance_db(name, date_time):
    # Connect to MySQL database
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="Delldollar@7",
        database = "attendance"
    )
    mycursor = mydb.cursor()

    # Check if the person has already signed in within the last 30 minutes
    thirty_minutes_ago = datetime.now() - timedelta(minutes=WAIT_TIME)
    sql = "SELECT * FROM attendance WHERE name = %s AND date_time > %s"
    val = (name, thirty_minutes_ago)
    mycursor.execute(sql, val)
    result = mycursor.fetchone()

    # If the person has already signed in within the last 30 minutes, do not insert new record
    if not result:
        # Insert new record in the database
        sql = "INSERT INTO attendance (name, date_time) VALUES (%s, %s)"
        val = (name, date_time)
        mycursor.execute(sql, val)
        mydb.commit()
        print(f"{name} signed in at {date_time}")

#encoding of face done here
def faceEncodings(img_list):
    encoding_lst=[]

    for image in img_list:
        encoding = face_recognition.face_encodings(image)[0]
        encoding_lst.append(encoding)
    
    return encoding_lst


known_encoding_lst = faceEncodings(images)

# captures face from webcam
cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()

    if not success:
        break

    test__face_locations = face_recognition.face_locations(img)
    test_encodings = face_recognition.face_encodings(img, test__face_locations)

    for encoded_face, location in zip(test_encodings,test__face_locations):
        matches= face_recognition.compare_faces( known_encoding_lst, test_encodings[0])
        face_distances = face_recognition.face_distance(known_encoding_lst,test_encodings[0])

        match_index= np.argmin(face_distances)

        if matches[match_index]:
            name = persons_names[match_index]

            y1,x2,y2,x1 = location
            cv2.rectangle(img,(x1,y1),(x2,y2),(255,0,0), 3)
            cv2.putText(img, name, (x1+8, y2-6), cv2.FONT_HERSHEY_COMPLEX, 1, (0,204,255),2)
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mark_attendance_db(name, date_time)

    cv2.imshow("Image",img)
    cv2.waitKey(1)

cap.release()
