from flask import Flask, request, jsonify, send_from_directory
import os
import json
import requests



app = Flask(__name__, static_folder='music')
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'music'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 여기에는 해당 action 이름이 와야한다.
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



@app.route('/stream/<path:filename>', methods=['GET', 'POST'])
def stream(filename):
    uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    return send_from_directory(directory=uploads, filename=filename)



@app.route('/answer.realtime_search', methods=['POST'])
def realtime():
    req = json.loads(request.data.decode('utf-8'))

    output = {}

    response = {}
    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output


    AudioPlayer = {}
    AudioPlayer['type'] = 'AudioPlayer.Play'


    audioItem = {}
    stream = {}
    stream['url'] = 'http://163.239.169.54:5001/stream/music1.mp4'  # 무슨 url ...?
    stream['offsetInMilliseconds'] = 0  # 노래 재생 시작지점 '0'이면 처음부터

    '''
    progressReport = {}
    progressReport['progressReportDelayInMilliseconds'] = 0
    progressReport['progressReportIntervalInMilliseconds'] = 0
    stream['progressReport'] = progressReport
    '''
    stream['progressReport'] = {}

    stream['token'] = 'something'  # 현재 stream을 나타내는 토큰?
    stream['expectedPreviousToken'] = 'something'   # 이전 stream?

    audioItem['stream'] = stream
    audioItem['metadata'] = None

    AudioPlayer['audioItem'] = audioItem

    AudioPlayer_ = {}
    AudioPlayer_['AudioPlayer'] = AudioPlayer

    response['directives'] = AudioPlayer_

    print(json.dumps(response, indent=4))

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



# ======================================================================================================================

def check_user(accessToken, response):
    response['resultCode'] = 'OK'
    with open('./info.json', 'r') as f:
        info = json.load(f)
        if info['accessToken'] != accessToken:
            print('다른 사용자')
            response['resultCode'] = 'error_diff_user'

def update_info_json_file(accessToken, action_name, current_recipe_step):
    with open('./info.json', 'w', encoding='utf-8') as f:
        info = {}
        info['accessToken'] = accessToken
        # 다음 action 입장에선 지금 이 action이 전 단계의 action이기 때문에 before_action 이라고 명칭.
        info['before_action'] = action_name
        info['recipe_step'] = current_recipe_step + 1
        json.dump(info, f, ensure_ascii=False, indent=4)



@app.route('/answer.recommend_recipe1', methods=['POST'])
def recommend_recipe1():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    action_name = req['action']['actionName']
    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'

    # 사용자의 accessToken과 레시피 step을 info.json 파일에 저장.
    # 이용하던 기존 사용자가 맞는지 확인, 몇번째 레시피 step인지 확인하기 위함.
    # before_action은 현재 action의 전 action이 무엇이었는지 확인하기 위함. (context 순서 확인용)
    with open('./info.json', 'w', encoding='utf-8') as f:
        info = {}
        info['accessToken'] = accessToken
        # 다음 action 입장에선 지금 이 action이 전 단계의 action이기 때문에 before_action 이라고 명칭.
        info['before_action'] = action_name
        # recipe step 1로 초기화
        info['recipe_step'] = 1
        json.dump(info, f, ensure_ascii=False, indent=4)



    output = {}
    output['fulfillment_recommend_recipe1'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주세요.'

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.recommend_recipe2', methods=['POST'])
def recommend_recipe2():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))
    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'



    # 동일한 사용자인지 확인
    check_user(accessToken, response)

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    # 한식, 중식, 양식, 분식
    food_kind = parameters['food_kind']['value']



    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    output['fulfillment_recommend_recipe2'] = '오늘의 ' + food_kind + '는 크림 스파게티 입니다. 안내를 원하시면 "안내해줘" 라고 말씀해주세요.'

    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.inform_ingredients', methods=['POST'])
def inform_ingredients():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken, response)


    with open('./info.json', 'r') as f:
        info = json.load(f)

    # 임시로 만든 simple.json 읽어오기
    with open('./sample.json', 'r') as f:
        sample = json.load(f)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    output['fulfillment_inform_ingredients'] = '필요한 재료는 ' + sample['simple_ingredients'] + ' 입니다. 자세한 설명을 들으시려면 "재료설명 들려줘" 라고 말씀해주시고, 바로 레시피 안내를 원하시면 "레시피 시작" 이라고 말씀해주세요.'

    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.detail_ingredients', methods=['POST'])
def detail_ingredients():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken, response)

    with open('./sample.json', 'r') as f:
        sample = json.load(f)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    output['fulfillment_detail_ingredients'] = sample['detail_ingredients'] + ' 이 필요합니다. 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'


    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)

@app.route('/answer.first_step_recipe', methods=['POST'])
def first_step_recipe():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken, response)

    with open('./info.json', 'r') as f:
        info = json.load(f)
        current_recipe_step = info['recipe_step']

    with open('./sample.json', 'r') as f:
        sample = json.load(f)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    # 첫번째 레시피 step 알림
    output['fulfillment_first_step_recipe'] = sample['recipe'][current_recipe_step] + ' 다 되시면 "아리아, [요리왕]에서 다음 안내 들려줘” 라고 이야기 해 주세요.'

    update_info_json_file(accessToken, action_name, current_recipe_step)


    response['version'] = '2.0'
    response['output'] = output
    # response['directives'] = {} 라고 하면 인식 못하고 에러 발생.
    response['directives'] = None

    return jsonify(response)



@app.route('/answer.next_step_recipe', methods=['POST'])
def next_step_recipe():
    response = {}
    req = json.loads(request.data.decode('utf-8'))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        # OAuth 를 사용하지 않는 경우
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken, response)

    with open('./info.json', 'r') as f:
        info = json.load(f)
        current_recipe_step = info['recipe_step']

    with open('./sample.json', 'r') as f:
        sample = json.load(f)


    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    output['fulfillment_next_step_recipe'] = sample['recipe'][current_recipe_step]

    # step 1 증가 후 info.json에 입력
    update_info_json_file(accessToken, action_name, current_recipe_step)

    # 마지막 recipe step 이라면
    if current_recipe_step + 1 == len(sample['recipe']):
        output['fulfillment_next_step_recipe'] += ' 이것이 요리의 마지막 안내입니다. 다시들으시려면 "아리아, [요리왕] 처음부터 안내" 라고 말해주세요. 저는 안내를 종료하겠습니다. 다음에 또 이용해주세요.'
    else:
        output['fulfillment_next_step_recipe'] += ' 다 되시면 "아리아, [요리왕]에서 다음 안내 들려줘” 라고 이야기 해 주세요.'

    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None



    return jsonify(response)

# ======================================================================================================================


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