from flask import Flask, request, Response
from enum import Enum
from bs4 import BeautifulSoup
import lxml.html
import requests
from random import randint
import flask

app = Flask(__name__)
logged_in = {}

class Login_Error(Enum):
    INVALID = -1
    TIME_OUT = -2
    NETWORKING_FAILURE = -3

def MOL_Login(session, user, password):
    payload = {'Username': user, 'Password': password, 'Connection': 'NA',
               'USER': user, 'SMAUTHREASON': '0', 'btnLogin': 'Login', 'FullURL': '',
               'target': 'https://motonline.mot-solutions.com/default.asp', 'SMAGENTNAME': '', 'REALMOID': '',
               'postpreservationdata': '', 'hdnTxtCancel': '', 'hdnTxtContinue': ''}
    MOL_url_GET_Login = 'https://businessonline.motorolasolutions.com/login.aspx?authn_try_count=0&contextType=external&username=string&initial_command=NONE&contextValue=%2Foam&password=sercure_string&challenge_url=https%3A%2F%2Foamprod.motorolasolutions.com%2FOAMSamlRedirect%2FOAMCustomRedircet.jsp&request_id=7662974962118535276&CREDENTIAL_CONTEXT_DATA=USER_ACTION_COMMAND%2CUSER_ACTION_COMMAND%2Cnull%2Chidden%3BUsername%2CUser+ID%2C%2Ctext%3BPassword%2CPassword%2C%2Cpassword%3B&PLUGIN_CLIENT_RESPONSE=UserNamePswdClientResponse%3DUsername+and+Password+are+mandatory&locale=en_US&resource_url=https%253A%252F%252Fbusinessonline.motorolasolutions.com%252F'
    MOL_url_POST_Login = 'https://oamprod.motorolasolutions.com/oam/server/auth_cred_submit'
    login_page_text = session.get(MOL_url_GET_Login).text
    login_html = lxml.html.fromstring(login_page_text)
    hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')
    for x in hidden_inputs:
        dict = x.attrib
        if 'value' in dict.keys():
            payload[dict['name']] = dict['value']
    login_request = session.post(MOL_url_POST_Login, data=payload)
    return login_request.text

def initiate_login(session, username, password):
    Login_attempt = MOL_Login(session, username, password)
    initial_login_parser = BeautifulSoup(Login_attempt, 'html.parser')

    if len(initial_login_parser.find_all('div', id='login-form')) != 0:
        return Login_Error.INVALID
    if len(initial_login_parser.find_all('p', class_='loginFailed')) != 0:
        return Login_Error.TIME_OUT
    return Login_attempt

def get_name_from_parser(parser):
    JSscript = parser.find_all('script', type="text/javascript")
    # print(JSscript[3].get_text().strip().startswith("var sBaseUrl = 'https://businessonline.motorolasolutions.com';"))
    for script in JSscript:
        if (script.get_text().strip().startswith("var sBaseUrl = 'https://businessonline.motorolasolutions.com';")):
            JSlogin_name = script.get_text().strip()
            find_string = 'var sLogonName = '
            JSlogin_name = JSlogin_name[JSlogin_name.index(find_string) + 1 + len(find_string):]
            JSlogin_name = JSlogin_name[:JSlogin_name.index("'")]
            return JSlogin_name

# @app.route('/Login', methods=['GET'])
# def check_logged_in():
#     if request.cookies.get('Logged_In_As') in logged_in.keys():
#         return 'logged_in'
#     return 'Not logged_in'

def getRandomLetters():
    output_string = ''
    sample = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    for index in range(0, 60):
        index = randint(0, len(sample) - 1)
        output_string +=  sample[index]
    return output_string

def display_main(cookie):
    user, name, session = logged_in[cookie]
    # return 'Welcome, ' + user + ', ' + name
    with open('HTML_pages/search_page.html', 'r') as html_file:
        html_string = html_file.read()
    return html_string.format(name)

@app.route('/Search', methods=['POST'])
def process_search():
    search_value = request.form['Input']
    return search_value

@app.route('/Main', methods=['POST', 'GET'])
def login_post():
    if request.method == 'GET':
        if request.cookies.get('Logged_In_Cookie') in logged_in.keys():
            return display_main(request.cookies.get('Logged_In_Cookie'))
        return 'Not logged_in'
    with requests.Session() as session:
        username = request.form['Username']
        password = request.form['Password']

        login_result = initiate_login(session, username, password)
        while login_result == Login_Error.TIME_OUT:
            login_result = initiate_login(session, username, password)
        if login_result == Login_Error.INVALID:
            return "Invalid Credentials, please try again!"
        name = get_name_from_parser(BeautifulSoup(login_result, 'html.parser'))

        cookie = getRandomLetters()
        logged_in[cookie] = username, name, session
        response = Response(display_main(cookie), 200)
        response.set_cookie('Logged_In_Cookie', cookie)

        return response

@app.route('/')
def get_initial_page():
    return flask.send_from_directory(directory='HTML_pages', filename='initial_page.html')

if __name__ == '__main__':
    app.run(port=80)