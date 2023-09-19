# THis is a proxy application that uses pyFreja.py to authenticate users
# and then forwards the request to the backend server.
# The proxy is a simple HTTP server that listens on port 8080.

import json
import threading
import time
from flask import Flask, request, redirect, render_template, session

from pyFreja import init_auth_request, get_auth_result_request, get_one_auth_result_request

app = Flask(__name__)

app.secret_key = "secret"
app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 # 24 hours


def authenticate(email):
    auth = init_auth_request("EMAIL",
                             email,
                             min_registration_level="BASIC",
                             attributes=["ALL_EMAIL_ADDRESSES"]
                             ).json()
    auth_ref = auth["authRef"]
    auth_result = get_one_auth_result_request(auth_ref).json()
    while auth_result["status"] not in ["APPROVED", "CANCELED", "FAILED"]:
        auth_result = get_one_auth_result_request(auth_ref).json()
        time.sleep(1)
    # If login was successful, pass the auth result to the index page
    if auth_result["status"] == "APPROVED":
        print("User authenticated")
        return auth_result
        #return template('index.html', auth_result=auth_result)

    # If login failed, return login page
    print("User not authenticated")
    return False


@app.route('/')
def home():
    print(session)
    if 'user' in session:
        return render_template('index.html', auth_result=session.get('freja_info'))
    return render_template('login.html')


# Define a route for the login form
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    print(f"Email: {email}")
    freja_info = authenticate(email)
    if freja_info:
        session['user'] = email
        session['freja_info'] = freja_info
        #return redirect('/')
    return redirect('/')
    #return render_template('error.html', message='Invalid username or password')

# Define a route for the logout button
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('freja_info', None)
    return redirect('/')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

