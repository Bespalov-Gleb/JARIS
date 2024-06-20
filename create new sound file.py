from db_pkg.database import Database
from db_pkg.models import User

db = Database()
user = db.get_query(User.login).filter(User.id == -1).first()
print(user)