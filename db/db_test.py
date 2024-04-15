from database import Database
from models import User

db = Database('sqlite:///test.db')

test_user = User(
    id=1,
    login='Jonh Shiteater',
    password='123 ',
    openai_token='123',
    picovoice_token='123',
    eden_token='123'
)

test_users = [
    User(
        id=2,
        login='Jonh Shitfucker',
        password='123 ',
        openai_token='123',
        picovoice_token='123',
        eden_token='123'),
    User(
        id=3,
        login='Jonh Shitducker',
        password='123 ',
        openai_token='123',
        picovoice_token='123',
        eden_token='123'
    ),
    User(
        id=4,
        login='Jonh Shitgainer',
        password='123 ',
        openai_token='123',
        picovoice_token='123',
        eden_token='123'
    )
]

db.add(test_user)

print(db.get_query(User).all())
