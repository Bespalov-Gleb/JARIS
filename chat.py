from db_pkg.database import Database
from db_pkg.models import User
#TEST 12345

db = Database()
utd = db.get_query(User).filter(User.id == -1).one()
