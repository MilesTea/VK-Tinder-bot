import os
import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
class UsersDb:
	def __init__(self):
		self.working_dir = os.getcwd()
		self.engine = sq.create_engine(f'sqlite:///{self.working_dir}\\database.db')
		self.Session = sessionmaker(bind=self.engine)
		self.session = self.Session()
		Base.metadata.create_all(self.engine)

	def add(self, user_id):
		try:
			user1 = Users(user_id=user_id)
			self.session.add(user1)
			self.session.commit()
		except:
			print('cant add')

	def delete(self, user_id):
		try:
			self.session.query(Users).filter(Users.user_id == user_id).delete()
			self.session.commit()
		except:
			print('cant delete')

	def delete_all(self):
		try:
			self.session.query(Users).delete()
			self.session.commit()
		except:
			print('cant delete')

	def check(self, user_id=None):
		try:
			if user_id:
				if self.session.query(Users).filter_by(user_id=user_id).first():
					return True
				else:
					return False
			else:
				if self.session.query(Users).first():
					return True
				else:
					return False
		except:
			print('cant_check')




'''	
working_dir = os.getcwd()
engine = sq.create_engine(f'sqlite:///{working_dir}\\database.db')
Session = sessionmaker(bind=engine)
session = Session()
'''


Base = declarative_base()
class Users(Base):
	__tablename__ = 'users'
	user_id = sq.Column(sq.Integer, primary_key=True)

# Base.metadata.create_all(engine)









'''
result = Session().query(Users).first()
print(result)
session.commit()

user1 = Users(user_id=1234)
session.add(user1)
session.commit()

result = Session().query(Users).first()
print(result.user_id)
session.commit()

# Session.close_all()
# result = Session().query(Users).delete()
session.query(Users).filter(Users.user_id == '1234').delete()
session.commit()

result = Session().query(Users).first()
print(result)
session.commit()
'''


'''
CREATE TABLE users (
    user_id INTEGER NOT NULL PRIMARY KEY
);
'''


if __name__ == '__main__':
	db = UsersDb()
	db.delete_all()
	print(db.check())