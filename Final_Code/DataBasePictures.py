"""
שם: רועי פירן
הפרויקט: הפרויקט הוא מערכת לשיתוף/עריכה/ניהול תמונות
שם המסמך: מאגר נתונים של תמונות
תיאור: קובץ זה יוצר טבלה שבה יהיה אפשר לשמור תמונות או יותר נכון את המיקום שלהם על המחשב
מפני שהתמונות עצמן נשמרות בתיקיה על המחשב שבו השרת ירוץ
"""
import sqlite3

# Connect to the database
conn = sqlite3.connect('picture_database.db')

# Create the pictures table
conn.execute('''CREATE TABLE PICTURES
             (ID INTEGER PRIMARY KEY AUTOINCREMENT,
             NAME TEXT,
             FILE_PATH TEXT,
             Version INTEGER);''')

# Close the connection
conn.close()
