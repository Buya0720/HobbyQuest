
from flask import Flask, jsonify, make_response, render_template, request, session, redirect, url_for
from calendar_ import db, TimeSlot

app = Flask(__name__, template_folder="./templates")
app.config['SECRET_KEY'] = "f7G@k8!r^V2jL&x9*ZbQ0$uP#nT1mW"
app.config['APPLICATION_ROOT'] = '/src'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timeslots.db'

db.init_app(app)
with app.app_context():
    db.create_all()

@app.context_processor
def navbar_in():
    navbar_ = [
        {"text": "Home", "url": url_for('location')},
        {"text": "Timeslot", "url": url_for('timeslots')},
        {"text": "Hobby", "url": url_for('hobby')},
        {"text": "Browse", "url": url_for('browse')},
        {"text": "My Events", "url": url_for('my_events')}
    ]
    return dict(navbar = navbar_)

@app.route('/')
def index():
    return redirect(url_for('location'))

@app.route('/user')
def user():
    return render_template()

@app.route('/timeslots')
def timeslots():
    if request.method == "POST":
        data = request.json
        slot_id = data.get('id')
        status = data.get('status')

        slot = TimeSlot.query.get(slot_id)
        if slot:
            slot.status = status
            db.status = status
            db.session.commit()
            return jsonify({'message': 'Success'}), 200
        return jsonify({'message': 'Slot not found'}), 404
    slots = TimeSlot.query.all()
    return render_template('timeslot_2.html', slots=slots)

@app.route('/locations', methods=['GET', 'POST'])
def location():
    if request.method == 'POST':
        session['location'] = {
            'city': request.form.get('city'),
            'latitude': request.form.get('latitude'),
            'longitude': request.form.get('longitude')
        }
        print(session['location'])
        return redirect(url_for('timeslot'))
    return render_template('location_page.html')

@app.route('/timeslot', methods=['GET', 'POST'])
def timeslot():
    if request.method == 'POST':
        data = request.json  # Get the JSON data sent from the front end
        session['timeslot'] = data  # Store the time slot data in session
        #return redirect(url_for('hobby'))  # Redirect to hobby selection after time slots are set
        print(session['timeslot'])
        print('location: ', session.get('location', {}))
        return jsonify({'status': session['timeslot']})  # Return a JSON response

    return render_template('timeslot_2.html')  # Render the time slot selection page

@app.route('/hobby', methods=['GET', 'POST'])
def hobby():
    if request.method == 'POST':
        try:
            data = request.json  # Get the JSON data sent from the front end

            session['hobby'] = data

            location_data = session.get('location', {})
            timeslot_data = session.get('timeslot', {})
            hobby_data = session.get('hobby', {})

            # For example, print it out for debugging
            all_data = {
            'locatoin': location_data,
            'timeslots': timeslot_data,
            'hobbies': hobby_data
            }

            print('all_data; ', all_data)
        except Exception as e:
            print(f"Error processing hobby data: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

        return jsonify({'Success': all_data})  # Return a JSON response
    return render_template('hobby_page.html')

@app.route('/myevents')
def my_events():
    return render_template('my_events.html')

@app.route('/browse')
def browse():
    return render_template('browse_events.html')

@app.errorhandler(404)
def page_not_found(error):
    resp = make_response(render_template('404.html'), 404)
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)