from flask import Flask, request, jsonify
import os
import json
import requests


app = Flask(__name__)
app.secret_key = os.urandom(24)



@app.route('/answer.weather', methods=['POST'])
def weather():
    req = json.loads(request.data.decode('utf-8'))
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    response = {}

    # output부분이 리턴되어서 출력된다.
    output = {}
    # output에는 Request의 모든 parameter가 포함되어야 한다. (value는 바뀔 수 있음)
    for param in parameters:
        output[param] = parameters[param]['value']

    output['fulfillment'] = '맑습니다.'


    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = {}

    return jsonify(response)


@app.route('/answer.music', methods=['POST'])
def music():
    req = json.loads(request.data.decode('utf-8'))
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    response = {}

    # output부분이 리턴되어서 출력된다.
    output = {}
    # output에는 Request의 모든 parameter가 포함되어야 한다. (value는 바뀔 수 있음)
    for param in parameters:
        output[param] = parameters[param]['value']
    output['fulfillment'] = '틀어드릴까요?'

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = {}

    return jsonify(response)





# 서버 연결 상태 점검용
@app.route('/health', methods=['GET', 'POST'])
def health_check():
    response = requests.get('http://163.239.169.54')

    if response.status_code == 200:
        return '200 OK'
    else:
        return response.status_code + ' Error'






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)