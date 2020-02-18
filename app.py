from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin
from flask_marshmallow import Marshmallow
import os
from flask_mail import Mail, Message

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///meeting.sqlite"  # path to database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Top Secret'

app.config['TESTING'] = False

# email configuration

app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '67047c3e7f5964'
app.config['MAIL_PASSWORD'] = 'f651cea5353f8c'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEBUG'] = True
app.config['MAIL_SUPPRESS_SENDER'] = False  # IF APP IS IN TESTING MODE,IT WONT SEND EMAILS TO RECEIPIENTS
app.config['MAIL_ASCII_ATTACHMENTS'] = False

mail = Mail(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "File_Download_Upload/static/images"

app.config['IMAGE_UPLOAD'] = "E:\class\Meeting\static\images"

db = SQLAlchemy(app)
ma = Marshmallow(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def format_date(date_string):
    return datetime.strptime(date_string, '%Y/%m/%d %H:%M').date()


def format_slash_date(date_string):
    return datetime.strptime(date_string, '%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M')


def format_hyphen_date(date_string):
    return datetime.strptime(date_string, '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M')


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
    image = db.Column(db.String(100), nullable=True)
    booked = db.Column(db.Boolean, default=False)
    time_booked = db.Column(db.DateTime())
    meetings = db.relationship("Meeting")


# serialize room table
class RoomSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'capacity', 'location',
                  'booked', 'time_booked')

        model = Room


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
@login_required
def create_room():
    if request.form and request.files:
        # grab form data
        name = request.form.get('roomname')
        capacity = request.form.get('roomcapacity')
        location = request.form.get('roomlocation')

        uploaded_image = request.files['roomimage']
        filename = secure_filename(uploaded_image.filename)

        # image upload
        uploaded_image.save(os.path.join(app.config["IMAGE_UPLOAD"], filename))
        image = "{}/{}".format("images", filename)

        room = Room(name=name, capacity=capacity, location=location, image=image)

        db.session.add(room)
        db.session.commit()
        flash('Room has been successfully added!')
        return redirect(url_for('get_rooms'))  # after succesful upload

    return render_template('room/create.html', title='Create')


@app.route('/room/display', methods=['GET', 'POST'])
@login_required
def get_rooms():
    rooms = Room.query.all()  # get all products from db
    return render_template('room/display.html', rooms=rooms, title="Display")


@app.route('/display/<int:room_id>/')  # handling a single product
@login_required
def detail(room_id):
    # get a product with the above id
    room = Room.query.get(room_id)
    return render_template('room/detail.html', room=room, title="Details")


@app.route('/lookup-rooms', methods=['GET', 'POST'])
def lookup_rooms():
    time_from = request.args.get('time_from')
    time_to = request.args.get('time_to')
    time_from_param = '{}{}'.format(format_hyphen_date(time_from), ':00.000000')
    time_to_param = '{}{}'.format(format_hyphen_date(time_to), ':00.000000')

    rooms_list = db.engine.execute(
        "select r.* from room r where r.id not in (select room_id from meeting m where m.timefrom "
        "<= :time_from_param AND m.timeto >= :time_to_param);",
        {'time_from_param': time_from_param, 'time_to_param': time_to_param})

    rooms_schema = RoomSchema(many=True)

    results = rooms_schema.dump(rooms_list, many=True)
    return {"rooms": results, "time_from": time_from_param, "time_to": time_to_param}


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
        flash('your room has been successfully updated')
        return redirect('/room/update/{}/'.format(room_id))

    return render_template('room/update.html', room=room, title="RoomUpdate")


@app.route('/room/delete/<int:room_id>/')
def delete(room_id):
    room = Room.query.get(room_id)

    db.session.delete(room)
    db.session.commit()

    return redirect('/room/display')



@app.route('/meeting/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    if request.form:
        room_id = request.form.get('meetingroom')
        description = request.form.get('meetingdescription')
        timefrom = request.form.get('startdate_datepicker')
        timeto = request.form.get('enddate_datepicker')
        invites = request.form.getlist('invites[]')

        time_from = format_slash_date(timefrom)
        time_to = format_slash_date(timeto)

        # get room then room id
        room = Room.query.filter_by(id=room_id).first()

        # create a Meeting object
        meeting = Meeting(room=room, description=description, room_id=room.id, timefrom=time_from, timeto=time_to)

        db.session.add(meeting)
        db.session.commit()
        send_mail(invites, time_from, time_to, room.name)
        flash('Meeting Scheduled!')
        return redirect(url_for('schedule'))
    rooms_list = Room.query.all()
    user_list = User.query.all()

    return render_template('meeting/schedule.html', title='Schedule', rooms=rooms_list, users=user_list)


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if request.form:
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        passwordHash = generate_password_hash(password)

        user = User(name=name, username=username, email=email, password=passwordHash)

        db.session.add(user)
        db.session.commit()
        # if not len(password) >= 8:
        #     flash("password must be atleast 8 Characters in length")

        return redirect(url_for('login'))
    return render_template('signup.html', title="SignUp")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    # return SessionUser.find_by_session_id(user_id)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.form:

        password = request.form.get('password')
        email = request.form.get('email')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            # flash('You were successfully logged in', 'alert alert-success')
            return redirect(url_for('index'))
        flash('Your login credentials are not correct, try again or signup')
        return redirect(url_for('login'))
    return render_template('login.html', title="Login")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


def send_mail(recipients, timeform, timeto, room_name):
    with mail.connect() as conn:
        msg = Message("Meetindroom schedule",
                      sender="pythonflask@mail.com",
                      recipients=recipients)
        msg.body = 'Hello,\nYou are invited to a meeting to be held at :'+ room_name +' ''' \
                   ' from  ' + timeform + ' to  ' + timeto + '@Meetingroom  '\

        conn.send(msg)
        return 'message set'


if __name__ == '__main__':
    app.run(port=3000, debug=True)
