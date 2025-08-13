from extensions import cpas as db
from datetime import datetime

class OnboardingApproval(db.Model):
    __tablename__ = 'onboarding_approval'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    tentative_start_date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(10))
    location = db.Column(db.String(100))
    employee_personal_email = db.Column(db.String(100), nullable=False)
    employee_company_email = db.Column(db.String(100))
    laptop_id = db.Column(db.String(50))
    asset_tag = db.Column(db.String(50))
    manager_vaco_id = db.Column(db.String(50))
    manager_email = db.Column(db.String(100), nullable=False)
    project_name = db.Column(db.String(100))
    hr_poc = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    teams_for_onboarding_json = db.Column(db.Text, nullable=False)
    approval_token = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    approval_timestamp = db.Column(db.DateTime)


class TeamStatus(db.Model):
    __tablename__ = 'team_status'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    tentative_start_date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(10))
    location = db.Column(db.String(100))
    employee_personal_email = db.Column(db.String(100), nullable=False)
    employee_company_email = db.Column(db.String(100))
    laptop_id = db.Column(db.String(50))
    asset_tag = db.Column(db.String(50))
    manager_vaco_id = db.Column(db.String(50))
    manager_email = db.Column(db.String(100))
    team = db.Column(db.String(50), nullable=False)
    project_name = db.Column(db.String(100))
    status = db.Column(db.String(20))
    jira_issue_key = db.Column(db.String(50))
    temp_id = db.Column(db.String(50))
    onboarding_status = db.Column(db.String(20))
    hr_poc = db.Column(db.String(100))
    job_title = db.Column(db.String(100))

    __table_args__ = (
        db.UniqueConstraint('employee_personal_email', 'tentative_start_date', 'team', name='_employee_date_team_uc'),
    )
