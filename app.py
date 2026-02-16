from flask import Flask, render_template, request, session, flash, redirect, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'khajukatli'

def get_db_connection():
    conn =mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        password = 'root',
        database = 'notesdb'
    )
    return conn

@app.route('/')
def Home():
    if 'user_id' in session:
        return redirect(url_for('viewall'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['uname'].strip()
        email = request.form['email'].strip()
        password = request.form['psd']

        if not username or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('register'))
        
        hashed_pw = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE username =%s', (username,))
        exists = cursor.fetchone()
        if exists:
            cursor.close()
            conn.close()
            flash("Username already taken. choose another one.", "danger")
            return redirect(url_for('register'))

        cursor.execute('INSERT INTO users(username, email, password) VALUES (%s, %s, %s)', (username, email, hashed_pw))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Registration Successfull! Please Login To Continue.", "Success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['uname'].strip()
        password = request.form['psd']

        if not username or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('login'))
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user['password'], password):

            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome, {user['username']}!", "success")
            return redirect(url_for('viewall'))
        else:
            flash("Invalid Credentials! Please Try Again.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been Logged Out Successfully.", "info")
    return redirect(url_for('login'))

@app.route('/addnote', methods=['GET', 'POST'])
def addnote():
    if 'user_id' not in session:
        flash("Please login first.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        user_id = session['user_id']

        if not title or not content:
            flash("Title and content cannot be empty.", "danger")
            return redirect(url_for('addnote'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notes (title, content, user_id) VALUES (%s, %s, %s)",
            (title, content, user_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Note created successfully!", "success")

        
        return redirect(url_for('viewall'))

    return render_template('addnote.html')


@app.route('/viewall')
def viewall():
    if 'user_id' not in session:
        flash("Please Login To Continue.", "danger")
        return render_template('login.html')
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, title, content, created_at FROM notes WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    notes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("viewall.html", notes=notes)

@app.route('/viewnotes/<int:note_id>')
def viewnotes(note_id):
     if 'user_id' not in session:
        flash("Please Login To Continue.", "danger")
        return redirect(url_for('login'))
     user_id = session['user_id']
     conn = get_db_connection()
     cursor = conn.cursor(dictionary=True)
     cursor.execute('SELECT id, title, content, created_at FROM notes WHERE id = %s AND user_id = %s', (note_id, user_id))
     note = cursor.fetchone()
     cursor.close()
     conn.close()

     if not note:
         flash("Note not found.", "danger")
         return redirect(url_for('viewall'))
     return render_template('singlenote.html', note=note)


@app.route('/updatenote/<int:note_id>', methods=['GET', 'POST'])
def updatenote(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    
    cur.execute("SELECT id, title, content FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
    note = cur.fetchone()

    if not note:
        cur.close()
        conn.close()
        flash("You are not authorized to edit this note.", "danger")
        return redirect('/viewall')

    if request.method == 'POST':
      
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        if not title or not content:
            flash("Title and content cannot be empty.", "danger")
            return redirect(url_for('updatenote', note_id=note_id))

        
        cur.execute("UPDATE notes SET title = %s, content = %s WHERE id = %s AND user_id = %s",
                    (title, content, note_id, user_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Note updated successfully.", "success")
        return redirect('/viewall')

   
    cur.close()
    conn.close()
    return render_template('updatenote.html', note=note)

@app.route('/deletenote/<int:note_id>', methods=['POST'])
def deletenote(note_id):
    if 'user_id' not in session:
        flash("Please Login To Continue.", "danger")
        return redirect('/login')
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE user_id = %s AND id = %s', (user_id, note_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Note Deleted Successfully!", "info")
    return redirect('/viewall')




if __name__ == '__main__':
    app.run(debug=True)