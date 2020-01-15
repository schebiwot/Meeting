from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///meeting.sqlite"  # path to database

db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html', title='Meeting')


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=True)


@app.route('/room', methods=['GET', 'POST'])
def create_room():
    if request.form:
        # grab form data
        name = request.form.get('roomname')
        capacity = request.form.get('roomcapacity')
        location = request.form.get('roomlocation')

        # create a room instance/object
        room = Room(Roomname=name, capacity=capacity, location=location)

        db.session.add(room)
        db.session.commit()
        flash('Room has been successfully added!', 'alert alert-success')
        return redirect(url_for('getrooms'))  # after succesful upload
        # room = Room(name=name, capacity=capacity, location=location)

    return render_template('room.html', title='All Rooms')


if __name__ == '__main__':
    app.run(port=5000, debug=True)
