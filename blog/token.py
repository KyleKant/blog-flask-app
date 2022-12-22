from itsdangerous import URLSafeTimedSerializer
from flask import current_app


def generate_confirmation_token(email):
    config = current_app.config
    serializer = URLSafeTimedSerializer(config['SECRET_KEY'])
    return serializer.dumps(email, salt=config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    config = current_app.config
    serializer = URLSafeTimedSerializer(config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token, max_age=expiration, salt=config['SECURITY_PASSWORD_SALT'])
    except:
        return False
    return email
