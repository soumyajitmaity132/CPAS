from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Change this to a strong, random key

@app.route('/')
def index():
    """Renders the login page."""
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """Handles login form submission."""
    username = request.form['username']
    password = request.form['password']

    # Simple hardcoded credentials for demonstration
    if username == 'root' and password == 'pass':
        session['logged_in'] = True
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password. Please try again.', 'danger')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Renders the dashboard page if the user is logged in."""
    if 'logged_in' in session and session['logged_in']:
        return render_template('daskboard.html') # Note: your file is named daskboard.html
    else:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Logs out the user."""
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) # debug=True for development, set to False in production