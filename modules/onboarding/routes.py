from flask import Blueprint, request, jsonify, session, render_template
from . import onboarding_bp
from modules.onboarding.core import get_onboarding_list, create_onboarding_entry

# @onboarding_bp.route('/', methods=['GET'])
# def onboarding_home():
#         role = session.get('role', {})
#         return render_template('dashboard.html',role=role)

@onboarding_bp.route('/', methods=['GET'])
def get_onboardings():
    # Example role check from session
    if 'user_id' not in session or not session.get('role', {}).get('is_employee', False):
        return jsonify({'error': 'Unauthorized'}), 403

    onboardings = get_onboarding_list()
    return jsonify(onboardings), 200

@onboarding_bp.route('/', methods=['POST'])
def add_onboarding():
    role = session.get('role', {})
    if not (role.get('is_admin') or role.get('is_manager') or role.get('is_hr')):
        return jsonify({'error': 'Insufficient permissions'}), 403

    data = request.get_json()
    success = create_onboarding_entry(data)
    return jsonify({'success': success}), 201 if success else 500
