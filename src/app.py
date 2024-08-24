from flask import Flask, make_response, render_template, request

app = Flask(__name__, template_folder="./templates")
app.config['SECRET_KEY'] = "f7G@k8!r^V2jL&x9*ZbQ0$uP#nT1mW"
app.config['APPLICATION_ROOT'] = '/src'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user')
def user():
    return render_template()

@app.route('/timeslots')
def timeslot():
    return render_template('timeslot.html')

@app.route('/locations')
def locations():
    return render_template('location_page.html')

@app.route('/hobby')
def locations():
    return render_template('hobby_page.html')

@app.errorhandler(404)
def page_not_found(error):
    resp = make_response(render_template('404.html'), 404)
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)