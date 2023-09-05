import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = ROOT_DIR + r'\personal_password_manager.sqlite3'
VALID_EMAIL_PATTERN = '^[_a-z0-9-]+(\\.[_a-z0-9-]+)*@[a-z0-9-]+(\\.[a-z0-9-]+)*(\\.[a-z]{2,4})$'
