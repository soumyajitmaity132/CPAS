import csv
from io import StringIO
import secrets
import random
import string
import json
import re
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, session, Blueprint
import MySQLdb.cursors
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_migrate import Migrate
from jira import JIRA
from db_session import SessionLocal
from config import Config 
from extensions import db
from config import get_db_connection
from mysql.connector import Error




onboarding_bp = Blueprint(
    'onboarding',
    __name__,
    template_folder='templates'
)

class TeamStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    tentative_start_date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(10), nullable=True) 
    location = db.Column(db.String(100), nullable=True)
    employee_personal_email = db.Column(db.String(100), nullable=False, unique=False) 
    employee_company_email = db.Column(db.String(100), nullable=True)
    laptop_id = db.Column(db.String(50), nullable=True)
    asset_tag = db.Column(db.String(50), nullable=True)
    manager_vaco_id = db.Column(db.String(50), nullable=True)
    manager_email = db.Column(db.String(100))
    team = db.Column(db.String(50), nullable=False) 
    project_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default="pending") 
    jira_issue_key = db.Column(db.String(50), nullable=True)
    temp_id = db.Column(db.String(50), nullable=True) 
    onboarding_status = db.Column(db.String(20), default="initiated")
    hr_poc = db.Column(db.String(100), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('employee_personal_email', 'tentative_start_date', 'team', name='_employee_date_team_uc'),
    )

class OnboardingApproval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    tentative_start_date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(10), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    employee_personal_email = db.Column(db.String(100), nullable=False)
    employee_company_email = db.Column(db.String(100), nullable=True)
    laptop_id = db.Column(db.String(50), nullable=True)
    asset_tag = db.Column(db.String(50), nullable=True)
    manager_vaco_id = db.Column(db.String(50), nullable=True)
    manager_email = db.Column(db.String(100), nullable=False)
    project_name = db.Column(db.String(100), nullable=True)
    hr_poc = db.Column(db.String(100), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    teams_for_onboarding_json = db.Column(db.Text, nullable=False)

    approval_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default="pending", nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)
    approval_timestamp = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<OnboardingApproval {self.id} - {self.first_name} {self.last_name} ({self.status})>"


def connect_to_jira():
    """Connects to Jira and returns the JIRA client."""
    options = {'server': Config.JIRA_URL}
    return JIRA(options=options, basic_auth=(Config.JIRA_EMAIL, Config.JIRA_API_TOKEN))


def create_jira_issue(summary, description, team, assignee_email):
    """Creates a Jira issue and transitions it to 'To Do' if not already."""
    jira_client = connect_to_jira()

    issue_dict = {
        'project': {'key': Config.JIRA_PROJECT_KEY},
        'summary': summary,
        'description': description,
        'issuetype': {'name': 'Task'},
        'labels': [team.lower()]
    }

    if assignee_email:
        try:
            user = jira_client.search_users(query=assignee_email, maxResults=1)
            if user:
                issue_dict['assignee'] = {'id': user[0].accountId}
        except Exception as e:
            print(f"Could not find Jira user for {assignee_email}: {e}")

    issue = jira_client.create_issue(fields=issue_dict)

    transitions = jira_client.transitions(issue)

    to_do_transition = next((t for t in transitions if t['to']['name'].lower() == "to do"), None)

    if to_do_transition:
        jira_client.transition_issue(issue, to_do_transition['id'])

    return issue.key


def transition_issue_to_status(issue_key, target_status_name):
    jira_client = connect_to_jira()  
    transitions = jira_client.transitions(issue_key)
    for t in transitions:
        if t['to']['name'].lower() == target_status_name.lower():
            jira_client.transition_issue(issue_key, t['id'])
            print(f"Issue {issue_key} transitioned to '{target_status_name}'")
            return
    print(f"No transition found for status '{target_status_name}' on issue {issue_key}")


def delete_jira_issue(issue_key):
    jira_client = connect_to_jira()
    jira_client.issue(issue_key).delete()


mail = Mail()


def send_email(app, subject, recipients, body=None, sender=None, cc=None, html=None):
    with app.app_context():
        msg = Message(subject=subject, recipients=recipients)
        msg.sender = sender if sender else app.config['MAIL_DEFAULT_SENDER']
        if cc:
            msg.cc = cc

        msg.body = body if body is not None else ''
        if html:
            msg.html = html
        mail.send(msg)


def get_next_working_day_10am():
    today = datetime.now()
    next_day = today + timedelta(days=1)
    while next_day.weekday() >= 5: 
        next_day += timedelta(days=1)
    return next_day.replace(hour=10, minute=0, second=0, microsecond=0)


def generate_temp_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) 


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
mail.init_app(app)
migrate = Migrate(app, db)


@onboarding_bp.route('/', methods=['GET'])
def index():
    return render_template('onboard_dashboard.html')

@onboarding_bp.route('/admin_onboarding', methods=['GET', 'POST'])
def admin_onboarding():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        tentative_start_date = request.form.get("tentative_start_date")
        shift = request.form.get('shift')
        location = request.form.get('location')
        employee_personal_email = request.form.get('employee_personal_email')
        employee_company_email = request.form.get('employee_company_email')
        laptop_id = request.form.get('laptop_id')
        asset_tag = request.form.get('asset_tag')
        manager_vaco_id = request.form.get('manager_vaco_id')
        manager_email = request.form.get('manager_email')
        project_name = request.form.get('project_name')
        hr_poc = request.form.get('hr_poc')
        job_title = request.form.get('job_title')

        errors = []
        email_regex = r"^[^@]+@[^@]+\.[^@]+$"

        # Validate required fields
        if not first_name:
            errors.append("First name is required.")
        if not last_name:
            errors.append("Last name is required.")
        if not job_title:
            errors.append("Job title is required.")
        if not tentative_start_date:
            errors.append("Start date is required.")
        else:
            try:
                # Validate date format
                datetime.strptime(tentative_start_date, "%Y-%m-%d")
            except ValueError:
                errors.append("Invalid date format for start date.")

        if not employee_personal_email or not re.match(email_regex, employee_personal_email):
            errors.append("Invalid personal email.")
        if manager_email and not re.match(email_regex, manager_email):
            errors.append("Invalid manager email.")

        # Stop if errors found
        if errors:
            for err in errors:
                flash(err, "danger")
            return redirect("/admin_onboarding")

        # Check for existing pending approval in DB
        existing_approval_request = OnboardingApproval.query.filter_by(
            employee_personal_email=employee_personal_email,
            tentative_start_date=tentative_start_date,
            status='pending'
        ).first()

        existing_team_status = TeamStatus.query.filter_by(
            employee_personal_email=employee_personal_email,
            tentative_start_date=tentative_start_date
        ).first()

        if existing_team_status:
            flash("An onboarding entry for this employee on this start date already exists in the system.", 'warning')
            return redirect(url_for('onboarding.admin_onboarding'))

        # Prepare onboarding teams and approval token
        teams_for_onboarding = ['IT', 'Security', 'Transport', 'HR']
        approval_token = secrets.token_urlsafe(32)

        new_approval_request = OnboardingApproval(
            first_name=first_name,
            last_name=last_name,
            tentative_start_date=tentative_start_date,
            shift=shift,
            location=location,
            employee_personal_email=employee_personal_email,
            employee_company_email=employee_company_email,
            laptop_id=laptop_id,
            asset_tag=asset_tag,
            manager_vaco_id=manager_vaco_id,
            manager_email=manager_email,
            project_name=project_name,
            hr_poc=hr_poc,
            job_title=job_title,
            teams_for_onboarding_json=json.dumps(teams_for_onboarding),
            approval_token=approval_token,
            status='pending',
            timestamp=datetime.utcnow(),
            approval_timestamp=None
        )

        try:
            db.session.add(new_approval_request)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Database error: {e}", "danger")
            return redirect("/admin_onboarding")

        approval_link = url_for('onboarding.approve_onboarding', token=approval_token, _external=True)
        reject_link = url_for('onboarding.reject_onboarding', token=approval_token, _external=True)

        try:
            start_date_fmt = datetime.strptime(tentative_start_date, "%Y-%m-%d").strftime('%B %d, %Y')
        except Exception:
            start_date_fmt = tentative_start_date

        manager_approval_email_html = f"""
        <html>
        <body>
        <h3>Onboarding Approval Request</h3>
        <p>Dear Manager ({manager_email.split('@')[0].title()}),</p>
        <p>An onboarding request has been submitted for your approval:</p>
        <ul>
            <li><b>Employee Name:</b> {first_name} {last_name}</li>
            <li><b>Tentative Start Date:</b> {start_date_fmt}</li>
            <li><b>Job Title:</b> {job_title if job_title else 'N/A'}</li>
            <li><b>Employee Personal Email:</b> {employee_personal_email}</li>
            <li><b>Employee Company Email:</b> {employee_company_email if employee_company_email else 'N/A'}</li>
            <li><b>Location:</b> {location}</li>
            <li><b>Shift:</b> {shift}</li>
            <li><b>Project Name:</b> {project_name if project_name else 'N/A'}</li>
            <li><b>HR POC:</b> {hr_poc if hr_poc else 'N/A'}</li>
            <li><b>Teams Involved:</b> {', '.join(teams_for_onboarding)}</li>
        </ul>
        <p>Please review the details and click on one of the options below to proceed:</p>
        <p style="margin-top: 25px;">
            <a href="{approval_link}" style="background-color: #28a745; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-right: 15px;">&#10004; Approve Onboarding</a>
            <a href="{reject_link}" style="background-color: #dc3545; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">&#10060; Reject Onboarding</a>
        </p>
        <p style="margin-top: 25px; font-size: 0.9em; color: #555;">This request will remain pending until your action.</p>
        <p>Best Regards,<br>Onboarding Automation System</p>
        </body>
        </html>
        """

        send_email(app,
                   f"ACTION REQUIRED: Onboarding Approval for {first_name} {last_name}",
                   [manager_email],
                   html=manager_approval_email_html)

        flash(
            f'Onboarding request for {first_name} {last_name} submitted for manager approval. An email has been sent to {manager_email}.',
            'info')
        return redirect(url_for('onboarding.index'))

    return render_template('admin_onboarding.html')



@onboarding_bp.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files.get('csv_file')
    if not file:
        flash('No file selected', 'danger')
        return redirect(url_for('onboarding.index'))

    try:
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        count = 0
        for row in reader:
            approval_token = secrets.token_urlsafe(32)
            tentative_start_date = datetime.strptime(row['tentative_start_date'], '%Y-%m-%d').date()
            approval_request = OnboardingApproval(
                first_name=row['first_name'],
                last_name=row['last_name'],
                tentative_start_date=tentative_start_date,
                shift=row.get('shift'),
                location=row.get('location'),
                employee_personal_email=row['employee_personal_email'],
                employee_company_email=row.get('employee_company_email'),
                laptop_id=row.get('laptop_id'),
                asset_tag=row.get('asset_tag'),
                manager_vaco_id=row.get('manager_vaco_id'),
                manager_email=row['manager_email'],
                project_name=row.get('project_name'),
                hr_poc=row.get('hr_poc'),
                job_title=row.get('job_title'),
                teams_for_onboarding_json=json.dumps(['IT', 'HR', 'Security', 'Transport']),
                approval_token=approval_token,
                status='pending'
            )
            db.session.add(approval_request)
            approval_link = url_for('onboarding.approve_onboarding', token=approval_token, _external=True)
            reject_link = url_for('onboarding.reject_onboarding', token=approval_token, _external=True)

            manager_approval_email_html = f"""
            <html>
            <body>
            <h3>Onboarding Approval Request</h3>
            <p>Dear Manager ({row['manager_email'].split('@')[0].title()}),</p>
            <p>An onboarding request has been submitted for your approval:</p>
            <ul>
                <li><b>Employee Name:</b> {row['first_name']} {row['last_name']}</li>
                <li><b>Tentative Start Date:</b> {row['tentative_start_date']}</li>
                <li><b>Job Title:</b> {row['job_title']}</li>
                <li><b>Employee Personal Email:</b> {row['employee_personal_email']}</li>
                <li><b>Location:</b> {row['location']}</li>
                <li><b>Shift:</b> {row['shift']}</li>
                <li><b>Project Name:</b> {row['project_name']}</li>
            </ul>
            <p>Please click one of the following:</p>
            <p style="margin-top: 25px;">
                <a href="{approval_link}" style="background-color: #28a745; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-right: 15px;">✅ Approve</a>
                <a href="{reject_link}" style="background-color: #dc3545; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">❌ Reject</a>
            </p>
            <p style="margin-top: 25px; font-size: 0.9em; color: #555;">This request will remain pending until your action.</p>
            <p>Best Regards,<br>Onboarding Automation System</p>
            </body>
            </html>
            """

            send_email(app,
                       f"ACTION REQUIRED: Onboarding Approval for {row['first_name']} {row['last_name']}",
                       [row['manager_email']],
                       html=manager_approval_email_html)

            count += 1
        db.session.commit()
        flash(f'Successfully uploaded {count} onboarding requests.', 'success')
    except Exception as e:
        flash(f'Error processing file: {e}', 'danger')

    return redirect(url_for('index'))


@onboarding_bp.route('/onboarding/approve/<token>', methods=['GET'])
def approve_onboarding(token):
    approval_request = OnboardingApproval.query.filter_by(approval_token=token, status='pending').first()

    if not approval_request:
        flash('Invalid or expired approval link, or request already processed.', 'danger')
        return render_template('approval_status.html',
                               message='Invalid or expired approval link, or request already processed.',
                               status='error')

    try:
        approval_request.status = 'approved'
        approval_request.approval_timestamp = datetime.now()
        db.session.add(approval_request)
        db.session.commit()

        first_name = approval_request.first_name
        last_name = approval_request.last_name
        tentative_start_date = approval_request.tentative_start_date
        shift = approval_request.shift
        location = approval_request.location
        employee_personal_email = approval_request.employee_personal_email
        employee_company_email = approval_request.employee_company_email
        laptop_id = approval_request.laptop_id
        asset_tag = approval_request.asset_tag
        manager_vaco_id = approval_request.manager_vaco_id
        manager_email = approval_request.manager_email
        project_name = approval_request.project_name
        hr_poc = approval_request.hr_poc
        job_title = approval_request.job_title
        teams_for_onboarding = json.loads(approval_request.teams_for_onboarding_json)

        temp_id = generate_temp_id()

        jira_issue_keys = []
        jira_base_url = Config.JIRA_URL + "/browse/"

        onboarding_common_details = {
            'first_name': first_name,
            'last_name': last_name,
            'tentative_start_date': tentative_start_date,
            'shift': shift,
            'location': location,
            'employee_personal_email': employee_personal_email,
            'employee_company_email': employee_company_email,
            'laptop_id': laptop_id,
            'asset_tag': asset_tag,
            'manager_vaco_id': manager_vaco_id,
            'manager_email': manager_email,
            'project_name': project_name,
            'temp_id': temp_id,
            'onboarding_status': 'initiated',
            'hr_poc': hr_poc,
            'job_title': job_title
        }

        for team_name in teams_for_onboarding:
            status_entry = TeamStatus(
                **onboarding_common_details,
                team=team_name,
                status="pending"
            )
            db.session.add(status_entry)

            summary = f"{team_name} Onboarding Task for {first_name} {last_name} (Start Date: {tentative_start_date.strftime('%Y-%m-%d')})"
            description = f"""
            New employee onboarding request for {first_name} {last_name}.
            Employee Personal Email: {employee_personal_email}
            Employee Company Email: {employee_company_email if employee_company_email else 'N/A'}
            Job Title: {job_title if job_title else 'N/A'}
            Manager Email: {manager_email}
            Manager Vaco ID: {manager_vaco_id if manager_vaco_id else 'N/A'}
            Tentative Start Date: {tentative_start_date.strftime('%Y-%m-%d')}
            Shift: {shift}
            Location: {location}
            Project Name: {project_name if project_name else 'N/A'}
            Temporary ID: {temp_id}
            HR POC: {hr_poc if hr_poc else 'N/A'}
            """
            team_email_recipient = {
                'IT': Config.IT_EMAIL_RECIPIENT,
                'HR': Config.HR_EMAIL_RECIPIENT,
                'Transport': Config.TRANSPORT_EMAIL_RECIPIENT,
                'Security': Config.SECURITY_EMAIL_RECIPIENT
            }.get(team_name, f"{team_name.lower()}@company.com")

            if team_name == 'IT':
                description += f"""

                **IT Specific Requirements:**
                - Provide a Windows laptop with standard configurations.
                - Install required software: Python, Jenkins.
                - Laptop ID: {laptop_id if laptop_id else 'TBD'}
                - Asset Tag: {asset_tag if asset_tag else 'TBD'}
                """
            elif team_name == 'Transport':
                description += f"""

                **Transport Specific Requirements:**
                - Arrange transport as per employee's location: {location}.
                """
            elif team_name == 'HR':
                description += f"""

                **HR Specific Requirements:**
                - Conduct orientation.
                - Process onboarding paperwork and documentation.
                - Provide Vaco ID and Phone ID.
                - HR POC: {hr_poc if hr_poc else 'N/A'}
                """
            elif team_name == 'Security':
                description += f"""

                **Security Specific Requirements:**
                - Grant necessary system access.
                - Conduct security briefing.
                """

            issue_key = create_jira_issue(summary, description, team_name, team_email_recipient)
            status_entry.jira_issue_key = issue_key
            jira_issue_keys.append(f"<a href='{jira_base_url}{issue_key}' target='_blank'>{issue_key}</a>")

            send_email(app,
                       f'New Employee Onboarding Task: {first_name} {last_name} - {team_name} Team',
                       [team_email_recipient],
                       html=f'<h3>Action Required for New Employee Onboarding</h3>'
                            f'<p>Please initiate onboarding tasks for <b>{first_name} {last_name}</b> ({employee_personal_email}) for the <b>{team_name}</b> team.</p>'
                            f'<p><b>Details:</b></p><ul>'
                            f'<li><b>Tentative Start Date:</b> {tentative_start_date.strftime("%Y-%m-%d")}</li>'
                            f'<li><b>Manager:</b> {manager_email} (Vaco ID: {manager_vaco_id if manager_vaco_id else "N/A"})</li>'
                            f'<li><b>Shift:</b> {shift}</li>'
                            f'<li><b>Location:</b> {location}</li>'
                            f'<li><b>Project Name:</b> {project_name if project_name else "N/A"}</li>'
                            f'<li><b>Jira Issue:</b> <a href="{jira_base_url}{issue_key}" target="_blank">{issue_key}</a></li>'
                            f'</ul><p><b>Specific tasks for your team:</b></p><p>{description.split("Requirements:</b><br/>")[-1].replace("<ul>", "").replace("</ul>", "")}</p>'
                            f'<p>Please update the Jira ticket as you progress.</p>',
                       cc=[manager_email])

        meet_link = "https://meet.google.com/abc-defg-hij"
        meet_time = get_next_working_day_10am().strftime("%A, %B %d, %Y at %I:%M %p")
        onboarding_doc_link = "onboarding_doc"
        daily_status_template_link = "daily_status_template_doc"

        employee_welcome_email_html = f"""
        <html>
        <body>
        <p>Welcome to the Vaco Binary family, {first_name}!</p>

        <p>We are excited to have you onboard &#127881;</p>

        <p>Your temporary employee ID is: <b>{temp_id}</b>. Please keep this handy for initial setups.</p>

        <p>Please join your manager for a Meet & Greet session:<br>
        &#128337; Time: {meet_time}<br>
        &#128279; Link: <a href="{meet_link}">{meet_link}</a></p>

        <p>As part of your onboarding, please create a copy of the following onboarding document and proceed accordingly:<br>
        &#128196; <a href="{onboarding_doc_link}">Onboarding Document (includes onboarding papers, reading materials, learning docs)</a></p>

        <p>You can find a daily status report template here: <a href="{daily_status_template_link}">{daily_status_template_link}</a></p>

        <p>Let us know if you have any questions.</p>

        <p>Cheers,<br>
        Vaco Ops Team</p>
        </body>
        </html>
        """
        send_email(app,
                   'Welcome to the VBS!',
                   [employee_personal_email],
                   html=employee_welcome_email_html,
                   cc=[manager_email])

        manager_jira_links_html = f"""
        <html>
        <body>
        <p>Dear {manager_email.split('@')[0].title()},</p>
        <p>Onboarding for <b>{first_name} {last_name}</b> ({employee_personal_email}) has been initiated following your approval.</p>
        <p>Here are the Jira tickets created for their onboarding tasks:</p>
        <ul>
            {''.join([f'<li>{link}</li>' for link in jira_issue_keys])}
        </ul>
        <p>Please track the progress of these tasks via the Jira links provided.</p>
        <p>Thank you,<br>
        Onboarding Automation System</p>
        </body>
        </html>
        """
        send_email(app,
                   f'Jira Tickets Created for New Onboarding: {first_name} {last_name}',
                   [manager_email],
                   html=manager_jira_links_html)

        db.session.commit()

        flash('Onboarding approved and all tasks initiated successfully!', 'success')
        return render_template('approval_status.html', message='Onboarding approved and tasks initiated successfully!',
                               status='success')

    except Exception as e:
        db.session.rollback()
        approval_request.status = 'pending'
        approval_request.approval_timestamp = None
        db.session.add(approval_request)
        db.session.commit()

        print(f"Error during onboarding approval process for token {token}: {e}")
        flash(
            'An error occurred during onboarding initiation. Please contact support. Request has been reverted to pending.',
            'danger')
        return render_template('approval_status.html',
                               message='An error occurred during onboarding initiation. Please contact support. Request has been reverted to pending.',
                               status='error')


@onboarding_bp.route('/onboarding/reject/<token>', methods=['GET'])
def reject_onboarding(token):
    approval_request = OnboardingApproval.query.filter_by(approval_token=token, status='pending').first()

    if not approval_request:
        flash('Invalid or expired rejection link, or request already processed.', 'danger')
        return render_template('approval_status.html',
                               message='Invalid or expired rejection link, or request already processed.',
                               status='error')

    try:
        approval_request.status = 'rejected'
        approval_request.approval_timestamp = datetime.now()
        db.session.add(approval_request)
        db.session.commit()

        admin_rejection_notification_email_html = f"""
        <html>
        <body>
        <h3>Onboarding Request Rejected</h3>
        <p>The onboarding request for <b>{approval_request.first_name} {approval_request.last_name}</b> has been <b>rejected</b> by the manager ({approval_request.manager_email}).</p>
        <p>No Jira tickets or onboarding tasks have been created.</p>
        <p>Please review the details in the system if needed.</p>
        </body>
        </html>
        """
        send_email(app,
                   f"Onboarding Request Rejected: {approval_request.first_name} {approval_request.last_name}",
                   [Config.ADMIN_EMAIL_RECIPIENT],
                   html=admin_rejection_notification_email_html)

        flash(
            f'Onboarding request for {approval_request.first_name} {approval_request.last_name} rejected successfully.',
            'info')
        return render_template('approval_status.html', message='Onboarding request rejected. No tasks initiated.',
                               status='rejected')

    except Exception as e:
        print(f"Error during onboarding rejection process for token {token}: {e}")
        flash('An error occurred during rejection. Please contact support.', 'danger')
        return render_template('approval_status.html',
                               message='An error occurred during rejection. Please contact support.', status='error')


@onboarding_bp.route('/manager-view', methods=['GET', 'POST'])
def manager_view():
    manager_emails = [row[0] for row in db.session.query(TeamStatus.manager_email).distinct().all() if row[0]]
    employees = [row[0] for row in db.session.query(TeamStatus.employee_personal_email).distinct().all() if row[0]]

    tasks = []
    selected_manager_email = request.form.get('manager_email') or request.args.get('manager_email')
    selected_employee_email = request.form.get('employee_personal_email') or request.args.get('employee_personal_email')

    query = TeamStatus.query

    if selected_manager_email:
        query = query.filter_by(manager_email=selected_manager_email)
    if selected_employee_email:
        query = query.filter_by(employee_personal_email=selected_employee_email)

    tasks = query.order_by(TeamStatus.tentative_start_date.desc(), TeamStatus.last_name.asc()).all()

    return render_template('manager_view.html',
                           tasks=tasks,
                           manager_emails=manager_emails,
                           employees=employees,
                           selected_manager_email=selected_manager_email,
                           selected_employee_email=selected_employee_email)


@onboarding_bp.route('/employee-view', methods=['GET', 'POST'])
def employee_view():
    employee_emails = [row[0] for row in db.session.query(TeamStatus.employee_personal_email).distinct().all() if
                       row[0]]
    tasks = []
    selected_employee_email = request.form.get('employee_personal_email') or request.args.get('employee_personal_email')

    if selected_employee_email:
        tasks = TeamStatus.query.filter_by(employee_personal_email=selected_employee_email).order_by(
            TeamStatus.tentative_start_date.desc()).all()

    return render_template('employee_view.html',
                           tasks=tasks,
                           employee_emails=employee_emails,
                           selected_employee_email=selected_employee_email)


@onboarding_bp.route('/team-status/<team_name>', methods=['GET', 'POST'])
def render_team_status_by_team(team_name):
    team_name = team_name.capitalize()
    if team_name == "Hr" or team_name == "It":
        team_name = team_name.upper()
    employees = [row[0] for row in db.session.query(TeamStatus.employee_personal_email).distinct().all() if row[0]]
    managers = [row[0] for row in db.session.query(TeamStatus.manager_email).distinct().all() if row[0]]

    query = TeamStatus.query

    if team_name != 'all':
        query = query.filter_by(team=team_name)

    if request.method == 'POST':
        employee_email = request.form.get('employee_personal_email')
        manager_email = request.form.get('manager_email')
    else:  
        employee_email = request.args.get('employee_personal_email')  
        manager_email = request.args.get('manager_email')

    if employee_email:
        query = query.filter_by(employee_personal_email=employee_email)
    if manager_email:
        query = query.filter_by(manager_email=manager_email)

    tasks = query.order_by(TeamStatus.tentative_start_date.desc(), TeamStatus.team.asc()).all()

    return render_template(
        'team_status.html',
        tasks=tasks,
        employees=employees,
        managers=managers,
        selected_team=team_name,
        selected_employee_email=employee_email,
        selected_manager_email=manager_email
    )


@onboarding_bp.route('/update-status', methods=['POST'])
def update_status():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    id = data.get('id')
    new_status = data.get('status')

    if not id or not new_status:
        return jsonify({'error': 'Missing id or status'}), 400

    task = db.session.get(TeamStatus, id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    old_status = task.status
    if old_status == new_status:
        return jsonify({'success': True, 'message': 'Status is already the same.'})

    task.status = new_status
    db.session.commit()

    if task.jira_issue_key:
        try:
            status_mapping = {
                'pending': 'To Do',
                'in-progress': 'In Progress',
                'complete': 'Done',
                'obsolete': 'Done'
            }
            jira_status = status_mapping.get(new_status.lower())
            if jira_status:
                transition_issue_to_status(task.jira_issue_key, jira_status)
        except Exception as e:
            print(f"Error updating Jira issue: {e}")

    manager_email_subject = f"Onboarding Task Status Update: {task.team} - {task.first_name} {task.last_name}"
    manager_email_body = f"""
    <html>
    <body>
    <p>Dear Manager,</p>
    <p>The status of an onboarding task for <b>{task.first_name} {task.last_name}</b> has been updated.</p>
    <ul>
        <li><b>Employee:</b> {task.employee_personal_email}</li>
        <li><b>Team:</b> {task.team}</li>
        <li><b>Old Status:</b> {old_status.replace('-', ' ').title()}</li>
        <li><b>New Status:</b> {new_status.replace('-', ' ').title()}</li>
        <li><b>Jira Issue:</b> <a href="{Config.JIRA_URL}/browse/{task.jira_issue_key}" target="_blank">{task.jira_issue_key}</a></li>
    </ul>
    <p>Please check the Jira ticket for more details.</p>
    <p>Thank you,<br>
    Onboarding Automation System</p>
    </body>
    </html>
    """
    send_email(app,
               manager_email_subject,
               [task.manager_email],
               html=manager_email_body,
               sender=Config.MAIL_DEFAULT_SENDER)

    return jsonify({'success': True, 'new_status_display': new_status.replace('-', ' ').title()})


@onboarding_bp.route('/feedback', methods=['GET'])
def feedback_form_page():
    return render_template('feedback_form.html')


@onboarding_bp.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    feedback_email = request.form['feedback_email']
    feedback_type = request.form['feedback_type']
    feedback_description = request.form['feedback_description']
    issue_summary = f"Feedback ({feedback_type}): from {feedback_email}"

    feedback_project_key = Config.JIRA_PROJECT_KEY
    issue_type = 'Task'

    description = f"""
    Feedback Type: {feedback_type}
    Submitted By: {feedback_email}

    Description:
    {feedback_description}
    """

    try:
        jira_client = connect_to_jira()
        issue_dict = {
            'project': {'key': feedback_project_key},
            'summary': issue_summary,
            'description': description,
            'issuetype': {'name': issue_type},
            'labels': ['feedback'],
        }
        issue = jira_client.create_issue(fields=issue_dict)
        jira_link = f"{Config.JIRA_URL}/browse/{issue.key}"

        # Make sure DEV_EMAIL_RECIPIENT is defined in Config
        # If not, add a placeholder in Config for testing, e.g., DEV_EMAIL_RECIPIENT = "your_dev_email@example.com"
        dev_email_subject = f"New Feedback Submitted: {issue_summary}"
        dev_email_body = f"""
        <html>
        <body>
        <p>A new feedback has been submitted via the onboarding portal.</p>
        <ul>
            <li><b>Submitted By:</b> {feedback_email}</li>
            <li><b>Feedback Type:</b> {feedback_type}</li>
            <li><b>Description:</b><pre>{feedback_description}</pre></li>
            <li><b>Jira Ticket:</b> <a href="{jira_link}" target="_blank">{issue.key}</a></li>
        </ul>
        <p>Please review the Jira ticket for details.</p>
        </body>
        </html>
        """
        send_email(app,
                   dev_email_subject,
                   [Config.DEV_EMAIL_RECIPIENT],
                   html=dev_email_body)

        send_email(app,
                   'Thank you for your feedback!',
                   [feedback_email],
                   html=f'<h3>Thank you for your feedback!</h3>'
                        f'<p>We have received your feedback regarding "{feedback_type}".</p>'
                        f'<p>A Jira ticket has been created for tracking: <a href="{jira_link}" target="_blank">{issue.key}</a></p>'
                        f'<p>We appreciate your input.</p>'
                        f'<p>Best Regards,<br>Onboarding Automation Team</p>')

        return redirect(url_for('onboarding.feedback_form_page', feedback='success'))
    except Exception as e:
        print(f"Error creating Jira feedback ticket or sending email: {e}")
        return redirect(url_for('onboarding.feedback_form_page', feedback='error'))


@onboarding_bp.route("/admin-dashboard")
def admin_dashboard():
    selected_team = request.args.get("team")
    selected_status = request.args.get("status")
    selected_employee_email = request.args.get("employee_email")
    selected_employee_name = request.args.get("employee_name")  # NEW

    query = TeamStatus.query

    if selected_team:
        query = query.filter_by(team=selected_team)
    if selected_status:
        query = query.filter_by(status=selected_status)
    if selected_employee_email:
        query = query.filter_by(employee_personal_email=selected_employee_email)
    if selected_employee_name:
        first, last = selected_employee_name.split(' ', 1) if ' ' in selected_employee_name else (selected_employee_name, '')
        query = query.filter(
            db.or_(
                db.func.concat(TeamStatus.first_name, ' ', TeamStatus.last_name) == selected_employee_name,
                TeamStatus.first_name == selected_employee_name  # fallback for first name only match
            )
        )

    onboardings = query.order_by(TeamStatus.tentative_start_date.desc()).all()

    all_data = TeamStatus.query.all()
    stats = {
        "total": len(all_data),
        "pending": sum(1 for d in all_data if d.status == "pending"),
        "in_progress": sum(1 for d in all_data if d.status == "in-progress"),
        "complete": sum(1 for d in all_data if d.status == "complete"),
        "obsolete": sum(1 for d in all_data if d.status == "obsolete"),
    }

    teams = sorted(set(d.team for d in all_data if d.team))
    employee_emails = sorted(set(d.employee_personal_email for d in all_data if d.employee_personal_email))
    employee_names = sorted(
        set(f"{d.first_name} {d.last_name}" for d in all_data if d.first_name and d.last_name)
    ) 

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        onboardings=onboardings,
        teams=teams,
        employee_emails=employee_emails,
        employee_names=employee_names,  
        selected_team=selected_team,
        selected_status=selected_status,
        selected_employee_email=selected_employee_email,
        selected_employee_name=selected_employee_name 
    )

@onboarding_bp.route('/manual-onboarding')
def manual_onboarding():
    return render_template('dashboard.html')

@onboarding_bp.route('/auto-onboard')
def auto_onboard():
    return "Auto Onboard page coming soon!"


