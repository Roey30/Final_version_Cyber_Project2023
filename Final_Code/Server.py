"""
שם: רועי פירן
הפרויקט: הפרויקט הוא מערכת לשיתוף/עריכה/ניהול תמונות
שם המסמך: צד שרת
תיאור: הקובץ הזה מבצע את כל הפעולות שמתרחשות מאוחרי הקלעים
הוא בעצם יוצר את התקשורת עם הצד לקוח בכל פעם שצד לקוח צריך גישה
למאגר הנתונים הוא שולח הודעה לצד שרת והצד שרת מחזיר לו את המידע שהוא צריך
"""
import io
import os
import socket
import ssl
import pickle
import hashlib
from _thread import *
from PIL import Image
import sqlite3


# CONSTANTS:
# CONNECTIONS VARIABLES:
IP_ADDR = '0.0.0.0'
PORT = 8443
QUEUE_LEN = 1
PACKET_LEN = 1024
CERT_FILE = 'certificate.crt'
KEY_FILE = 'privateKey.key'

# LISTS OF VARIABLES:
PASSWORD_STORAGE = []  # pa
USERNAME_STORAGE = []  # us
PICTURES_STORAGE = []  # pi

# CONNECTIONS PROTOCOL:
# FIRST MESSAGE: LENGTH=THE MESSAGE LENGTH
# SECOND MESSAGE: THE IMAGE ITSELF
PICTURES_TO_SERVER_PROTOCOL = 'PTSP'
PICTURES_TO_CLIENT_PROTOCOL = 'PTCP'
LOG_IN_CLIENT_PROTOCOL = 'LICP'
SIGN_UP_CLIENT_PROTOCOL = 'SICP'
CLIENT_BACK_TO_START_PROTOCOL = 'CBTSP'
CLIENT_LOG_OUT_PROTOCOL = 'QUIT'


# THREAD VARIABLES:
gDict = {}
userDict = {}

PHOTOS_SAVED_FILE = 'PhotosToServer'


def sign_up(username, password, c):
    """
    הפעולה הזאת אחראית על הכנסת המשתמש שנרשם למאגר נתונים.
    היא מקבל את שם המשתמש והסיסמא מהצד לקוח (FRON – END)  מהמשתמש והיא בודקת אם השם משתמש
    והסיסמא נכונים (אם לא קיים כבר משתמש עם אותו שם)
אם הם נכונים היא מכניסה את הנתונים ומאגר נתונים והיא מעדכנת את הצד לקוח, אם הם שגויים היא לא
מכניסה למאגר הנתונים והיא מודיע לצד לקוח שהנתונים שגויים וינסה שנית.
    :param username: שם משתמש
    :param password: סיסמא
    :param c: חיבור צפציפי עם הצד לקוח
    """
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    exist = exist_signup_check(username)
    if exist == 'True':
        c.sendall(pickle.dumps('True'))
    elif exist == 'False':
        c.sendall(pickle.dumps('False'))
        connection_data = sqlite3.connect("username_password_storage.db")
        cursor = connection_data.cursor()

        cursor.execute("INSERT INTO username_password_storage (name, password) VALUES (?, ?)",
                       (username, hashed_password))
        connection_data.commit()
        connection_data.close()

        PASSWORD_STORAGE.append(hashed_password)
        USERNAME_STORAGE.append(username)
        print(f'The username storage: {USERNAME_STORAGE}')
        print(f'The password storage: {PASSWORD_STORAGE}')


def log_in(username, password, c):
    """
    הפעולה הזאת אחראית על בדיקת המשתמש שרוצה להיכנס לעמוד התמונות.
    היא מקבל את שם המשתמש והסיסמא מהצד לקוח (FRON – END)  מהמשתמש והיא בודקת אם שם המשתמש
 והסיסמא נכונים (אם אין משתמש שכבר נכנס עם אותו שם משתמש וסיסמא והוא כרגע בפנים) אם הם נכונים היא שולחת לצד לקוח שהכל בסדר
    והוא מכניס את המשתמש לעמוד התמונות, אם הם שגויים היא מודיע על כך לצד לקוח,
  ישנם כמה מצבים של שגיאה: 1. השם משתמש או הסיסמא לא נמצאים במאגר נתונים. 2. יש כבר משתמש עם הנתונים האלה שהוא בפנים.
    :param username: שם משתמש
    :param password: סיסמא
    :param c: חיבור צפציפי עם הצד לקוח
    """
    global USERNAME_STORAGE, PASSWORD_STORAGE
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    place = 0
    username_password_exist = pickle.dumps('False')
    connection_data = sqlite3.connect("username_password_storage.db")
    cursor = connection_data.cursor()

    cursor.execute("SELECT * FROM username_password_storage")
    users = cursor.fetchall()

    connection_data.close()

    for u in users:
        if username == u[1]:
            print("Username - True")
            if hashed_password == users[place][2]:
                print("Password - True")
                print(len(userDict))
                if len(userDict) == 0:
                    print('User - True')
                    username_password_exist = pickle.dumps('True')
                    userDict[c] = username
                else:
                    for u_name in list(userDict):
                        if username == userDict[u_name]:
                            print('User - Taken')
                            username_password_exist = pickle.dumps('Taken')
                        else:
                            print('User - True')
                            username_password_exist = pickle.dumps('True')
                            userDict[c] = username
                break
        place += 1
    c.sendall(username_password_exist)


def client_back_to_start(c):
    """
    הפעולה הזאת אחראית כאשר המשתמש חוזר לעמוד הראשי בצד הלקוח. כאשר המשתמש חוזר לעמוד הראשי הצד לקוח מודיע
    זאת לצד שרת והצד שרת קורה לפעולה הזאת והיא מורידה את המשתמש שחזר לעמוד הראשי מרשימת המשתמשים שנמצאים כרגע בעמוד התמונות.
    :param c: חיבור צפציפי עם הצד לקוח
    """
    global userDict

    if len(userDict) != 0:
        print(f"The user {userDict[c]} back to start page")
        print(f"The user {userDict.pop(c)} has disconnected")
    else:
        return


def exist_signup_check(username):
    """
    הפעולה הזאת אחראית לבדוק האם השם משתמש שנרשם למערכת בפעולה sign_up כבר במאגר נתונים או לא.
    :param username: שם משתמש
    """
    exist = False
    conn = sqlite3.connect("username_password_storage.db")
    name = conn.cursor()

    name.execute("SELECT * FROM username_password_storage")
    users = name.fetchall()

    for entry_user_name in users:
        if username == entry_user_name[1]:
            exist = True
    if exist:
        conn.close()
        return 'True'
    else:
        conn.close()
        return 'False'


def serverside_picture_handle(c, number_pictures):
    """
    הפעולה הזאת אחראית לקבל את כל התמונות שהצד לקוח שולח לצד שרת.
    היא שומרת את התמונות בתיקיה על המחשב ואת המיקום שלהם בתור מסד הנתונים של הפרויקט.
    :param c: חיבור צפציפי עם הצד לקוח
    :param number_pictures: מספר תמונות
    """
    try:
        number_pictures = int(number_pictures)
        while number_pictures > 0:
            c.sendall(pickle.dumps('ok'))
            data = c.recv(4096).decode()
            data = data.split("=")
            length = int(data[1])
            image_data = b''
            while True:
                if len(image_data) == length:
                    c.sendall(pickle.dumps("got it"))
                    picture_name = pickle.loads(c.recv(1024))
                    version = pickle.loads(c.recv(1024))
                    print("hellllllooooo")
                    image_data += data
                    break
                else:
                    data = c.recv(4096)
                    image_data += data

            # Convert the image data into an image object
            picture_name = picture_name.split('.')
            picture_name = picture_name[0]
            image = Image.open(io.BytesIO(image_data))

            image_path = f"{PHOTOS_SAVED_FILE}/{picture_name}.JPG"
            image.save(image_path, format='PNG')
            connection_data = sqlite3.connect("picture_database.db")
            cursor = connection_data.cursor()

            cursor.execute("INSERT INTO PICTURES (NAME, FILE_PATH, Version) VALUES (?, ?, ?)",
                           (picture_name, image_path, version))
            connection_data.commit()
            connection_data.close()
            PICTURES_STORAGE.append((image_path, picture_name))
            number_pictures -= 1
            print(PICTURES_STORAGE)
        c.sendall(pickle.dumps('Finish'))
    except EOFError and ConnectionResetError as err:
        print(f"Something came up2: {err}")
        print(f"connection {gDict.pop(c)} Has disconnected")
        if len(userDict) != 0:
            print(f"{userDict.pop(c)} Has disconnected")
        else:
            print(f"No user was connected")


def clientside_picture_handle(c):
    """
    הפעולה הזאת אחראית לשלוח את כל התמונות שיש לה במאגר הנתונים לצד לקוח.
    :param c: חיבור צפציפי עם הצד לקוח
    """
    try:
        connection_data = sqlite3.connect("picture_database.db")
        cursor = connection_data.cursor()

        cursor.execute("SELECT * FROM PICTURES")
        pictures = cursor.fetchall()

        connection_data.close()
        msg_pic_to_client = str(len(pictures))
        print(msg_pic_to_client, type(msg_pic_to_client))
        c.sendall(pickle.dumps(msg_pic_to_client))
        print(f"storage paths: {pictures} ")
        for i in pictures:
            with open(i[2], 'rb') as f:
                image_data = f.read()
            if pickle.loads(c.recv(1024)) == 'ok':
                data_to_client = f"LENGTH={len(image_data)}"
                c.sendall(data_to_client.encode())
                c.sendall(image_data)
            if pickle.loads(c.recv(1024)) == 'got it':
                c.sendall(pickle.dumps(i[1]))
                c.sendall(pickle.dumps(i[3]))
    except EOFError and ConnectionResetError as err:
        print(f"Something came up2: {err}")
        print(f"connection {gDict.pop(c)} Has disconnected")
        if len(userDict) != 0:
            print(f"{userDict.pop(c)} Has disconnected")
        else:
            print(f"No user was connected")


def receive(c):
    """
    הפעולה הזאת בעצם אחראית על כל הודעה שהצד שרת מקבל מהצד לקוח.
   כל הודעה מתקבלת ועוברת בדיקה כדי לראות מה הצד לקוח רוצה ולפי כך הצד שרת משיג לו את המידע.
    :param c: חיבור צפציפי עם הצד לקוח
    """
    try:
        while True:
            # data received from client
            data = c.recv(1024)
            if data == b'':
                print('Bye')
                print(f"connection {gDict.pop(c)} Has disconnected")
                if len(userDict) != 0:
                    print(f"{userDict.pop(c)} Has disconnected")
                # lock released on exit
                # print_lock.release()
                exit_thread()
                break
            data = pickle.loads(data)
            print(f'The data: {data}')
            # print(f'The data decoded: {data[0].decode()} , {data[1].decode()}')
            if data[0] == LOG_IN_CLIENT_PROTOCOL:
                log_in(data[1], data[2], c)
            elif data[0] == SIGN_UP_CLIENT_PROTOCOL:
                sign_up(data[1], data[2], c)
            elif data[0] == PICTURES_TO_SERVER_PROTOCOL:
                serverside_picture_handle(c, data[1])
            elif data == PICTURES_TO_CLIENT_PROTOCOL:
                clientside_picture_handle(c)
            elif data == CLIENT_BACK_TO_START_PROTOCOL:
                client_back_to_start(c)
            if not data or data == CLIENT_LOG_OUT_PROTOCOL:
                print('Bye')
                print(f"connection {gDict.pop(c)} has disconnected")
                client_back_to_start(c)
                # lock released on exit
                # print_lock.release()
                exit_thread()
                break
            broadcast(c, data)
    except EOFError and ConnectionResetError as err:
        print(f"Something came up2: {err}")
        print(f"connection {gDict.pop(c)} Has disconnected")
        if len(userDict) != 0:
            print(f"{userDict.pop(c)} Has disconnected")
        else:
            print(f"No user was connected")
    finally:
        c.close()


def broadcast(c, data):
    """
    הפעולה הזאת אחראית לתת דוח מצב של כל החיבורים והמשתמשים שמחוברים לשרת באותו רגע נתון.
    זה שיש לדוגמא 10 חיבורים אומר שיש 10 משתמשים מחוברים,
    חשוב להזכיר כי ברגע שמשתמש יוצא לעמוד הבית הוא נחשב בחוץ אך עדיין מחובר לשרת כחיבור תקשורתי.
    :param c: חיבור צפציפי עם הצד לקוח
    :param data: המידע שהוא מקבל מהצד לקוח
    """
    # print(" | ".join(str(i) for i in gDict.values()))
    print(f"gDict: {gDict}")
    for connection in gDict:
        print(f"Connection: {gDict.get(connection)} | Data: {data}")
    if len(userDict) != 0:
        if c in userDict:
            print(f"User {userDict[c]} send => {data}")
            print("List of Users and their socket:")
        for u in userDict:
            print(f"socket: {u} user: {userDict[u]}")

    conn = sqlite3.connect('username_password_storage.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM username_password_storage")
    rows = cur.fetchall()

    for row in rows:
        print(row)
    cur.close()
    conn.close()


def main():
    """
    הפעולה הזאת היא אולי החשובה מכולם היא זאת שיוצרת את החיבור לצד לקוח,
    עוטפת את החיבור כדי למנוע פריצות ומתחילה את הסכרון תהליכם (threads).
    """
    # Local host: '127.0.0.1'

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CERT_FILE, KEY_FILE)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP_ADDR, PORT))
        # put the socket into listening mode
        server_socket.listen(QUEUE_LEN)
        print("socket is listening")
        ssocket = context.wrap_socket(server_socket, server_side=True)
        print("socket bound to port", PORT)

        try:
            # a forever loop until client wants to exit
            while True:
                # establish connection with client
                conn, addr = ssocket.accept()
                global gDict
                global userDict
                # Adds Socket / Connection to Dict
                gDict[conn] = addr

                print('Connected to :', addr[0], ':', addr[1])

                # receive(conn)
                start_new_thread(receive, (conn,))
        except ConnectionError and EOFError as err:
            print(f"Something came up : {err}")
            # Keyboard interrupt with CTRL + C, make sure to close active clients first
            # We never reach this line, but it feels good to have it
        finally:
            ssocket.close()
            quit()
    except socket.error as sock_err:
        print(sock_err)
    finally:
        server_socket.close()


if __name__ == '__main__':
    # Check if folder exists
    PHOTOS_SAVED_FILE = 'PhotosToServer'
    if not os.path.exists(PHOTOS_SAVED_FILE):
        # Create folder if it does not exist
        os.makedirs(PHOTOS_SAVED_FILE)

    connect_data = sqlite3.connect("username_password_storage.db")
    user = connect_data.cursor()

    user.execute("SELECT * FROM username_password_storage")
    entries = user.fetchall()

    print("Users DataBase:")
    print("ID - USERNAME - PASSWORD")
    for entry in entries:
        print(f"{entry[0]}: {entry[1]} - {entry[2]}")

    connect_data.close()

    connect_data = sqlite3.connect("picture_database.db")
    user = connect_data.cursor()

    user.execute("SELECT * FROM PICTURES")
    entries = user.fetchall()

    print("Photos DataBase:")
    print("ID - NAME - FILE_PATH - VALUES")
    for entry in entries:
        print(f"{entry[0]}: {entry[1]} - {entry[2]} - {entry[3]}")

    connect_data.close()
    main()
