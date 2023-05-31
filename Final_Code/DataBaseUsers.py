"""
שם: רועי פירן
הפרויקט: הפרויקט הוא מערכת לשיתוף/עריכה/ניהול תמונות
שם המסמך: מאגר נתונים של משתמשים
תיאור: קובץ זה יוצר טבלה בה יהיה אפשר לשמור את תכונות המשתמשים שנרשמים
התכונות הם: שם משתמש וסיסמא
"""
import sqlite3

# Connect to the database
username_password_storage = sqlite3.connect("username_password_storage.db")

# Create the pictures table
username_password_storage.execute("""CREATE TABLE IF NOT EXISTS username_password_storage (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT,
             password TEXT
             )""")

# Close the connection
username_password_storage.close()
