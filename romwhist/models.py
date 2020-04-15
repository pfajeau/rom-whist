from .extensions import db
from flask_login import UserMixin

################
# Hefrom flask_login import UserMixin
# Helper models
################


class BaseModel(db.Model):
    """
    Abstract model
    """

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, server_default=db.func.now())
    date_modified = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def update(self, **kwargs):
        for key, value in kwargs.items():
            try:
                getattr(self, key)
                setattr(self, key, value)
            except AttributeError:
                pass

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# TODO - Add your models here  e.g.
class User(BaseModel, UserMixin):
    __tablename__ = 'user'

    username = db.Column(db.String)
#    password = db.Column(db.String)
    authenticated = db.Column(db.Boolean, default=True)
