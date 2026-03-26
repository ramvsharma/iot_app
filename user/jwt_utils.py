import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "your-very-secure-and-secret-key"
ALGORITHM = "HS256"


def create_jwt_token(user):
    payload = {
        'user_id': user.user_id,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=30),
        'iat': datetime.now(timezone.utc),
        'iss': 'iot-application-provider'
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_jwt_token(token):
    try:
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_payload
    except jwt.ExpiredSignatureError as e:
        print("Token has expired:", e)
        return None
    except jwt.InvalidTokenError as e:
        print("Invalid token:", e)
        return None
