from flask import Flask, render_template, request, redirect, url_for, session
from db_session import SessionLocal, Base
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from modules.onboarding.app import onboarding_bp
from config import Config
from extensions import db, migrate

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

app.register_blueprint(onboarding_bp, url_prefix="/onboarding")

class Employee(Base):
    __tablename__ = "Employee"

    Id_user = Column(Integer, primary_key=True, index=True)
    Username = Column(String(100))
    Password = Column(String(255))
    Security_key = Column(String(250))
    Fullname = Column(String(100))
    is_admin = Column(Boolean, default=False)
    is_manager = Column(Boolean, default=False)
    is_hr = Column(Boolean, default=False)
    is_employee = Column(Boolean, default=True)
    is_recteam = Column(Boolean, default=False)
    Is_serving = Column(Boolean, default=True)
    Email = Column(String(100), unique=True)
    Employee_id = Column(String(100))
    Client_name = Column(String(100))
    Is_active = Column(Boolean, default=True)
    Created_at = Column(TIMESTAMP)
    Updated_at = Column(TIMESTAMP)

def get_user_from_db(username):
    db = SessionLocal()
    try:
        return db.query(Employee).filter_by(Username=username).first()
    finally:
        db.close()

def determine_role(user):
    if user.is_admin:
        return 'admin'
    elif user.is_hr:
        return 'hr'
    elif user.is_manager:
        return 'manager'
    elif user.is_recteam:
        return 'recruitmentteam'
    elif user.is_employee:
        return 'employee'
    return 'unknown'

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_from_db(username)

        if user and user.Password == password:
            session['user'] = user.Username
            session['role'] = determine_role(user)
            session['employee_id']=user.Employee_id
            session['is_recruiter']=user.is_recteam
            return redirect(url_for('main_dashboard'))
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)

@app.route('/main_dashboard')
def main_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('main_dashboard.html', user=session.get('user'), role=session.get('role'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
