from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS

app = Flask(__name__)

app.config['SECRET_KEY'] = '5f4dcc3b5aa765d61d8327deb882cf99' 

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/kanban_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' 
CORS(app) 

from app import routes, models

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))