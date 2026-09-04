from enum import unique
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import enum
import os.path
import os
from datetime import datetime, timezone

from flask_migrate import Migrate#, MigrateCommand   #pip install flask-migrate
import os

DO_MIGRATE = True
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "../mars_top.db")
#DB_FILE = '../../lh003reg.db' #specify db file to be migrate

db = SQLAlchemy()

if DO_MIGRATE:
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+DB_FILE
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

#https://blog.miguelgrinberg.com/post/fixing-alter-table-errors-with-flask-migrate-and-sqlite#:~:text=Run%20flask%20db%20downgrade.%20This%20will%20undo%20those,script%20and%20try%20again%20with%20batch%20mode%20enabled.
migrate = Migrate(app,db)
migrate.init_app(app,db,render_as_batch=True)
#manager = Manager(app)
#manager.add_command('db',MigrateCommand)

def create_db_app(dbName,appName=__name__):
    app= Flask(appName)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+dbName
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

'''
def create_database_app(filename=DEFAULT_DB_FILE):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+filename
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app
'''

ACCESS_OPT = ['RO','RW','W']
VISIBILITY_OPT = ['Public','Private','False','True']


#############################################
#        Rule waiver metadata table
#############################################

class RULE_WAIVER(db.Model):
    """Portable rule acknowledgements stored beside register business data."""

    __tablename__ = 'lsr_rule_waiver'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    fingerprint = db.Column(db.String(64), unique=True, nullable=False)
    severity = db.Column(db.String(16), nullable=False)
    code = db.Column(db.String(128), nullable=False)
    path = db.Column(db.Text, nullable=False)
    field = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)
    module_id = db.Column(db.Integer, nullable=True)
    register_id = db.Column(db.Integer, nullable=True)
    bit_id = db.Column(db.Integer, nullable=True)
    waived_at = db.Column(
        db.String(40),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).isoformat(),
    )


#############################################
#            BIT value table declaration
############################################
#rules
MAX_BIT_VALUE_DESC_LEN = 512

class BIT_VALUE(db.Model):
    __tablename__ = 'bit_value'
    id = db.Column(db.Integer,primary_key=True)
    value = db.Column(db.Integer,unique=False,nullable=False)
    desc = db.Column(db.String(MAX_BIT_VALUE_DESC_LEN),unique=False,nullable=False)
    bit_id = db.Column(db.Integer,db.ForeignKey('bit.id'),nullable=False)
    bit = db.relationship('BIT',backref=db.backref('bitvalues',lazy=True))

#############################################
#            BIT table declaration
############################################
#rules
MAX_NAME_STRING_LEN=10
MAX_KEY_STRING_LEN=32
MAX_DESC_STRING_LEN=256
MAX_ACCESS_STRING_LEN=10
MAX_VISIBILITY_STRING_LEN=10


class BIT(db.Model):
    __tablename__ = 'bit'
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String(MAX_NAME_STRING_LEN),unique=False,nullable=False)
    position = db.Column(db.Integer,unique=False,nullable=False)
    width = db.Column(db.Integer,unique=False,nullable=False)
    access = db.Column(db.String(MAX_ACCESS_STRING_LEN),unique=False,nullable=True)
    default_value = db.Column(db.Integer,unique=False,nullable=True)
    key = db.Column(db.String(MAX_KEY_STRING_LEN),unique=False,nullable=True)
    visibility = db.Column(db.String(MAX_VISIBILITY_STRING_LEN),unique=False,nullable=True)
    doc = db.Column(db.Text,unique=False,nullable=True)
    scan = db.Column(db.Integer,unique=False,nullable=True)
    set = db.Column(db.String(MAX_KEY_STRING_LEN),unique=False,nullable=True)
    clr = db.Column(db.String(MAX_KEY_STRING_LEN),unique=False,nullable=True)
    reg_id = db.Column(db.Integer,db.ForeignKey('reg.id'),nullable=False)
    reg = db.relationship('REG',backref=db.backref('bits',lazy=True, order_by='BIT.position'))


    #CheckConstraint('access in ACCESS_OPT',name='checkAccess')
    #CheckConstraint('visibility in VISIBILITY_OPT',name='checkVisibility')

#############################################
#            Register table declaration
############################################
#rules

class REG(db.Model):
    __tablename__ = 'reg'
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String(MAX_NAME_STRING_LEN),unique=False,nullable=False)
    address = db.Column(db.Integer,unique=False,nullable=False)
    width = db.Column(db.Integer,unique=False,nullable=False)
    access = db.Column(db.String(MAX_ACCESS_STRING_LEN),unique=False,nullable=True)
    default_value = db.Column(db.Integer,unique=False,nullable=True)
    desc = db.Column(db.String(MAX_DESC_STRING_LEN),unique=False,nullable=True)
    doc = db.Column(db.Text,unique=False,nullable=True)
    visibility = db.Column(db.Integer,unique=False,nullable=True)
    ate_trim = db.Column(db.Integer,unique=False,nullable=True)
    #retain = db.Column(db.Boolean,unique=False,nullable=True)

    module_id = db.Column(db.Integer,db.ForeignKey('module.id'),nullable=False)
    module = db.relationship('MODULE',backref=db.backref('regs',lazy=True, order_by='REG.address'))

    #CheckConstraint('access in ACCESS_OPT',name='checkAccess')
    #CheckConstraint('visibility in VISIBILITY_OPT',name='checkVisibility')
    #CheckConstraint('width < 32',name='width')

#############################################
#            Module(TOP) table declaration
############################################
#rules
MAX_BIT_NAME_STRING_LEN = 10

class MODULE(db.Model):
    __tablename__ = 'module'
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String(MAX_NAME_STRING_LEN),unique=False,nullable=False)
    address = db.Column(db.Integer,unique=False,nullable=False)
    desc = db.Column(db.String(MAX_DESC_STRING_LEN),unique=False,nullable=True)
    doc = db.Column(db.Text,unique=False,nullable=True)

if __name__ == '__main__':
    pass
    #manager.run()
    #command line operation
    #python regdb.py migrate db init
