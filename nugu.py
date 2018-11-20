from flask import Flask, request, jsonify, send_from_directory
import os
import json
import requests
import random



app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'music'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER




@app.route('/stream/<filename>', methods=['GET', 'POST'])
def stream(filename):
    print('root path : ' + app.root_path)
    uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    print('uploaded path : ' + str(uploads))
    print('filename : ' + filename)
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
    stream['url'] = 'http://163.239.169.54:5001/stream/music1.mp3'  # 무슨 url ...?
    stream['offsetInMilliseconds'] = 0  # 노래 재생 시작지점 '0'이면 처음부터

    '''
    progressReport = {}
    progressReport['progressReportDelayInMilliseconds'] = 0
    progressReport['progressReportIntervalInMilliseconds'] = 0
    stream['progressReport'] = progressReport
    '''
    stream['progressReport'] = None

    stream['token'] = 'something'  # 현재 stream을 나타내는 토큰?
    stream['expectedPreviousToken'] = 'something'   # 이전 stream?

    audioItem['stream'] = stream
    audioItem['metadata'] = None

    AudioPlayer['audioItem'] = audioItem


    response['directives'] = [AudioPlayer]

    print(json.dumps(response, indent=4))

    return jsonify(response)



# ======================================================================================================================
# 다양한 다음 단계 설명 유도 문장들
next_step_invoke = ['아리아, [요리왕]에서 다음 안내 들려줘',
                    '아리아, [요리왕]에서 다음 차례는 뭐야?',
                    '아리아, [요리왕]에서 다음엔 뭘 하면 될까?',
                    '아리아, [요리왕]에서 다음에 뭐해?']


# 레시피 설명 후에 나올 수 있는 액션들
possible_action_after_recipe = []
# 레시피 설명 전에 나올 수 있는 액션들
possible_action_before_recipe = ['answer.confirm_yes', 'answer.confirm_no', 'answer.ask_recipe', 'answer.inform_food_type']



def check_user(accessToken, response):
    response['resultCode'] = 'OK'
    with open('./info.json', 'r') as f:
        info = json.load(f)
        if info['accessToken'] != accessToken:
            print('다른 사용자')
            response['resultCode'] = 'error_diff_user'

def update_info_json_file(accessToken, action_name, current_recipe_step):
    # 사용자의 accessToken과 레시피 step을 info.json 파일에 저장.
    # 이용하던 기존 사용자가 맞는지 확인, 몇번째 레시피 step인지 확인하기 위함.
    # before_action은 현재 action의 전 action이 무엇이었는지 확인하기 위함. (context 순서 확인용)
    with open('./info.json', 'w', encoding='utf-8') as f:
        info = {}
        info['accessToken'] = accessToken
        # 다음 action 입장에선 지금 이 action이 전 단계의 action이기 때문에 before_action 이라고 명칭.
        info['before_action'] = action_name
        info['recipe_step'] = current_recipe_step
        json.dump(info, f, ensure_ascii=False, indent=4)


# ======================================================================================================================


@app.route('/answer.ask_recipe', methods=['POST'])
def ask_recipe():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    action_name = req['action']['actionName']
    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'

    # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
    update_info_json_file(accessToken, action_name, 0)


    output = {}
    output['fulfillment_ask_recipe'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주세요.'

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.inform_food_type', methods=['POST'])
def inform_food_type():
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
    food_type = parameters['food_type']['value']

    with open('./sample.json', 'r') as f:
        sample = json.load(f)


    with open('./info.json', 'w', encoding='utf-8') as f:
        info = {}
        info['accessToken'] = accessToken
        # 다음 action 입장에선 지금 이 action이 전 단계의 action이기 때문에 before_action 이라고 명칭.
        info['before_action'] = action_name
        # recipe step 1로 초기화
        info['recipe_step'] = 1
        json.dump(info, f, ensure_ascii=False, indent=4)


    # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
    update_info_json_file(accessToken, action_name, 0)


    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    #output['fulfillment_inform_food_type'] = '오늘의 ' + food_kind + '는 ' +  sample['food_name'] + '입니다.'
    #output['fulfillment_inform_food_type'] += ' 안내를 원하시면 "재료 안내해줘" 라고 말씀해주세요.'

    output['fulfillment_food_type'] = food_type
    output['fulfillment_food_name'] = sample['food_name']

    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)

'''
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


    output['fulfillment_inform_ingredients'] = '필요한 재료는 ' + sample['simple_ingredients'] + ' 입니다.'
    output['fulfillment_inform_ingredients'] += ' 자세한 설명을 들으시려면 "재료 자세히 알려줘" 라고 말씀해주시고,'
    output['fulfillment_inform_ingredients'] += ' 바로 레시피 안내를 원하시면 "레시피 시작" 이라고 말씀해주세요.'

    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)
'''


@app.route('/answer.ask_ingredients', methods=['POST'])
def ask_ingredients():
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

    with open('./info.json', 'r') as f:
        info = json.load(f)
        # ask_ingredients intent로 들어오기 전에 무슨 action이었는지 확인
        before_action = info['before_action']
        current_recipe_step = info['recipe_step']



    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    # 레시피 설명 시작 전
    if current_recipe_step == 0:
        output['fulfillment_ask_ingredients'] = sample['detail_ingredients'] + ' 이 필요합니다.'
        output['fulfillment_ask_ingredients'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'

        # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
        update_info_json_file(accessToken, action_name, 0)
    # 레시피 설명 도중
    else:
        output['fulfillment_ask_ingredients'] = sample['detail_ingredients'] + ' 입니다.'
        output['fulfillment_ask_ingredients'] += ' 현재 단계를 다시 들으시려면 "아리아, [요리왕]에서 방금 안내 다시 들려줘" 라고 이야기 해 주시고,'
        output['fulfillment_ask_ingredients'] += ' 다음 단계로 넘어가시려면 "아리아, [요리왕]에서 다음 안내 들려줘" 라고 이야기 해 주세요.'

        update_info_json_file(accessToken, action_name, current_recipe_step)


    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)




@app.route('/answer.start_recipe', methods=['POST'])
def start_recipe():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken, response)


    # 첫번째 step 이기때문에 1로 고정 설정
    current_recipe_step = 1

    with open('./sample.json', 'r') as f:
         sample = json.load(f)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    # 첫번째 레시피 step 알림
    output['fulfillment_start_recipe'] = sample['recipe'][current_recipe_step] + ' 다 되시면 ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'

    # 다음 단계로 넘어가니까 step + 1
    update_info_json_file(accessToken, action_name, current_recipe_step + 1)


    response['version'] = '2.0'
    response['output'] = output
    # response['directives'] = {} 라고 하면 인식 못하고 에러 발생.
    response['directives'] = None

    return jsonify(response)



@app.route('/answer.next', methods=['POST'])
def next():
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

    output['fulfillment_next'] = sample['recipe'][current_recipe_step]

    # step 1 증가 후 info.json에 입력
    update_info_json_file(accessToken, action_name, current_recipe_step + 1)

    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    # 마지막 recipe step 이라면
    if current_recipe_step + 1 == len(sample['recipe']):
        output['fulfillment_next'] += ' 이것이 요리의 마지막 안내입니다. 다시들으시려면 "아리아, [요리왕] 처음부터 안내" 라고 말해주세요. 저는 안내를 종료하겠습니다. 다음에 또 이용해주세요.'
    else:
        output['fulfillment_next'] += ' 다 되시면 ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'

    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None


    return jsonify(response)

'''
@app.route('/answer.explain_ingredients_again', methods=['POST'])
def explain_ingredients_again():
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


    with open('./info.json', 'w', encoding='utf-8') as f:
        info = {}
        info['accessToken'] = accessToken
        # 다음 action 입장에선 지금 이 action이 전 단계의 action이기 때문에 before_action 이라고 명칭.
        info['before_action'] = action_name
        info['recipe_step'] = current_recipe_step
        json.dump(info, f, ensure_ascii=False, indent=4)


    with open('./sample.json', 'r') as f:
        sample = json.load(f)


    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    output['fulfillment_explain_ingredients_again'] = sample['detail_ingredients'] + ' 입니다.'
    output['fulfillment_explain_ingredients_again'] += ' 현재 단계를 다시 들으시려면 "아리아, [요리왕]에서 방금 안내 다시 들려줘" 라고 이야기 해 주시고,'
    output['fulfillment_explain_ingredients_again'] += ' 다음 단계로 넘어가시려면 "아리아, [요리왕]에서 다음 안내 들려줘" 라고 이야기 해 주세요.'

    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)
'''

@app.route('/answer.repeat', methods=['POST'])
def repeat():
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


    update_info_json_file(accessToken, action_name, current_recipe_step)

    # 방금 전 단계를 가리키기 위해 -1
    current_recipe_step -= 1

    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    output['fulfillment_repeat'] = sample['recipe'][current_recipe_step] + ' 다 되시면 ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'


    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.start', methods=['POST'])
def start():
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
        # start intent로 들어오기 전에 무슨 action이었는지 확인
        before_action = info['before_action']
        current_recipe_step = info['recipe_step']

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    # 레시피 설명하기 전 처음으로 가고자 할 경우
    if current_recipe_step == 0:
        output['fulfillment_start'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주세요.'
        update_info_json_file(accessToken, action_name, 0)
    # 레시피 설명 도중 처음으로 가고자 할 경우
    else:
        output['fulfillment_start'] = '다른 레시피를 추천해드릴까요? "응" 또는 "아니" 로 말씀해주세요.'
        update_info_json_file(accessToken, action_name, current_recipe_step)



    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.confirm_yes', methods=['POST'])
def confirm_yes():
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
        # confirm_yes intent로 들어오기 전에 무슨 action이었는지 확인
        before_action = info['before_action']

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    if before_action == 'answer.start':
        output['fulfillment_confirm_yes'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주세요.'


    update_info_json_file(accessToken, action_name, 0)

    response['version'] = '2.0'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.confirm_no', methods=['POST'])
def confirm_no():
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
        # confirm_no intent로 들어오기 전에 무슨 action이었는지 확인
        before_action = info['before_action']


    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    if before_action == 'answer.start':
        output['fulfillment_confirm_no'] = '그럼 현재 레시피를 처음 단계부터 다시 알려드릴게요.'
        output['fulfillment_confirm_no'] += ' 레시피 설명을 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'


    update_info_json_file(accessToken, action_name, 0)

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