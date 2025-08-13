from flask import Blueprint

onboarding_bp = Blueprint(
    'onboarding',
    __name__,
    url_prefix='/onboarding',
    template_folder='templates'
)

from . import routes 
__all__ = ['onboarding_bp']

