from os import remove

from database import Database
from models import User


def test(path):
    try:
        db = Database(path)

        # test data
        test_user = User(
            id=None,
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

        # add test user and check it
        db.add(test_user)
        db.add(test_user)
        print(db.get_query(User).one())
        # assert db_pkg.get_query(User).all() == [test_user]

        # add more test users and use filter
        db.add(test_users)
        # assert db_pkg.get_query(User).filter(User.id == 1).one() == test_users

        user_to_delete = db.get_query(User).filter(User.login == 'Jonh Shitfudker').first()

    except:
        pass
    finally:
        # deletes db_pkg file
        remove(path.split('///')[1])


if __name__ == '__main__':
    test('sqlite:///test.db_pkg')
