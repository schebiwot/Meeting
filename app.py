from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///meeting.sqlite"  # path to database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Top secret'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def index():
    return render_template('index.html', title='Meeting')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    username = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.String(100), unique=False, nullable=False)
    password = db.Column(db.String(128), unique=False, nullable=False)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=True)
    booked = db.Column(db.Boolean, default=False)
    time_booked = db.Column(db.DateTime())
    meetings = db.relationship("Meeting")


class MyDateTime(db.TypeDecorator):
    impl = db.DateTime

    def process_bind_param(self, value, dialect):
        if type(value) is str:
            return datetime.strptime(value, '%Y/%m/%d %H:%M')
        return value


class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(100), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    room = db.relationship("Room")
    timefrom = db.Column(MyDateTime, nullable=False, default=datetime.utcnow())
    timeto = db.Column(MyDateTime, nullable=False, default=datetime.utcnow())


@app.route('/room/create', methods=['GET', 'POST'])
def create_room():
    if request.form:
        # grab form data
        name = request.form.get('roomname')
        capacity = request.form.get('roomcapacity')
        location = request.form.get('roomlocation')

        # create a room instance/object
        room = Room(name=name, capacity=capacity, location=location)

        db.session.add(room)
        db.session.commit()
        # flash('Room has been successfully added!', 'alert alert-success')
        return redirect(url_for('get_rooms'))  # after succesful upload
        # room = Room(name=name, capacity=capacity, location=location)

    return render_template('room/create.html', title='Create')


@app.route('/room/display', methods=['GET', 'POST'])
def get_rooms():
    rooms = Room.query.all()  # get all products from db
    return render_template('room/display.html', rooms=rooms,title="Display")


@app.route('/display/<int:room_id>/')  # handling a single product
def detail(room_id):
    # get a product with the above id
    room = Room.query.get(room_id)
    return render_template('room/detail.html', room=room,title="Details")


@app.route('/room/update/<int:room_id>/', methods=['GET', 'POST'])  # handling a single room
def update(room_id):
    room = Room.query.get(room_id)

    if request.form:
        name = request.form.get('roomname')
        capacity = request.form.get('roomcapacity')
        location = request.form.get('roomlocation')

        room.name = name
        room.capacity = capacity
        room.location = location

        db.session.commit()
        # flash('your room has been succes?sfully updated')
        # go back to the previous page
        return redirect('/room/update/{}/'.format(room_id))

    return render_template('room/update.html', room=room ,title="RoomUpdate")


@app.route('/room/delete/<int:room_id>/')
def delete(room_id):
    room = Room.query.get(room_id)

    db.session.delete(room)
    db.session.commit()

    return redirect('/room/display')


@app.route('/meeting/schedule', methods=['GET', 'POST'])
def schedule():
    if request.form:
        # date = request.form.get('meetingdate')
        room_id = request.form.get('meetingroom')
        description = request.form.get('meetingdescription')
        timefrom = request.form.get('timefrom')
        timeto = request.form.get('timeto')

        # get room then room id
        room = Room.query.filter_by(id=room_id).first()

        # create a Meeting instance/object
        meeting = Meeting(room=room, description=description, room_id=room.id, timefrom=timefrom, timeto=timeto)

        # #
        db.session.add(meeting)
        db.session.commit()
        # flash('Meeting has been successfully added!', 'alert alert-success')
        return redirect(url_for('schedule'))
    rooms_list = Room.query.all()
    return render_template('meeting/schedule.html', title='Schedule', rooms=rooms_list)


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if request.form:
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        password = generate_password_hash(password)



        user =User(name=name, username=username, email=email, password=password);

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html',title="SignUp")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.form:

        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if check_password_hash(password, password):
            login_user(user)
            # flash(u'You were successfully logged in', 'alert alert-success')
            return redirect(url_for('index'))
        # flash(u'Your login credentials are not correct, try again or signup', 'alert alert-danger')
        return redirect(url_for('login'))
    return render_template('login.html', title="Login")


if __name__ == '__main__':
    app.run(port=5000, debug=True)
