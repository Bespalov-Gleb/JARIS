from db_pkg.database import Database
from db_pkg.models import User

db = Database()
user_to_add = User(
            id=None,
            login='HYI',
            password='12345',
            openai_token='',
            picovoice_token='PICO',
            eden_token="EDEN",
            current_lang='en'
        )
db.add(user_to_add)
print(db.get_query(User).filter(User.login == 'HYI').all())