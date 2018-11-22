from flask import Flask, request, jsonify, send_from_directory
import os
import json
import requests
import random
import google.oauth2.credentials
from google.auth.transport.requests import AuthorizedSession
import smtplib
from email.mime.text import MIMEText

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
    stream['url'] = 'http://163.239.169.54:5001/stream/music1.mp3'
    # 노래 재생 시작지점 '0'이면 처음부터
    stream['offsetInMilliseconds'] = 0

    '''
    progressReport = {}
    progressReport['progressReportDelayInMilliseconds'] = 0
    progressReport['progressReportIntervalInMilliseconds'] = 0
    stream['progressReport'] = progressReport
    '''
    stream['progressReport'] = None

    stream['token'] = 'something'
    stream['expectedPreviousToken'] = 'something'

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


# 새로운 사용자인지 확인. 새로운 사용자면 info_user.json에 등록
def check_user(accessToken):
    is_new_user = 1
    is_exist_access_token = 0

    with open('./user_info.json', 'r') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                is_exist_access_token = 1
                break
            else:
                is_exist_access_token = 0

    # 기존에 user_info.json에 등록되지 않은 access token 이라면  "1. 새로운 사용자" (또는) "2. 기존 사용자의 access token 만료" 두가지 경우
    if is_exist_access_token == 0:
        user_email = get_user_email(accessToken)
        for each_user_info in user_info:
            # 기존에 등록되어 있던 이메일 이면 기존 사용자
            if each_user_info['user_email'] == user_email:
                is_new_user = 0
                break
            else:
                is_new_user = 1

        # 새로운 사용자인 경우
        if is_new_user == 1:
            new_user = {}
            new_user['accessToken'] = accessToken
            new_user['user_email'] = user_email


            # 새로운 사용자를 user_info 리스트에 추가
            user_info.append(new_user)
            # 그리고 user_info.json 파일 업데이트
            with open('./user_info.json', 'w', encoding='utf-8') as f:
                json.dump(user_info, f, ensure_ascii=False, indent=4)



def update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe):

    with open('./user_info.json', 'r') as f:
        try:
            user_info = json.load(f)
            for each_user_info in user_info:
                if each_user_info['accessToken'] == accessToken:
                    user_email = user_info['user_email']
        except:
            user_email = None


    with open('./user_info.json', 'r') as f:
        user_info = json.load(f)
        # 사용자 리스트 루프 돌면서
        for i, each_user_info in enumerate(user_info):
            # 해당 사용자 찾는다
            if each_user_info['accessToken'] == accessToken:
                temp = {}
                temp['accessToken'] = accessToken
                temp['before_action'] = action_name
                temp['selected_recipe'] = selected_recipe
                temp['recipe_step'] = current_recipe_step
                temp['user_email'] = user_email
                # 해당 사용자 정보 갱신
                user_info[i] = temp
                break


    # 사용자의 accessToken과 레시피 step을 user_info.json 파일에 저장.
    with open('./user_info.json', 'w', encoding='utf-8') as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4)



def get_user_email(accessToken):
    if accessToken == 'dev':
        user_email = None
        return user_email

    google_access_token = accessToken

    credentials = google.oauth2.credentials.Credentials(google_access_token)
    authed_session = AuthorizedSession(credentials)

    try:
        response_google = authed_session.get('https://www.googleapis.com/oauth2/v2/userinfo')
        user_data = response_google.content.decode('utf-8')
        user_data = json.loads(user_data)
        user_email = user_data['email']
    except:
        with open('./user_info.json', 'r') as f:
            user_info = json.load(f)
            for each_user_info in user_info:
                if each_user_info['accessToken'] == accessToken:
                    user_email = each_user_info['user_email']

    return user_email


def send_gmail_to_user(accessToken, selected_recipe, action_name, current_recipe_step):
    google_access_token = accessToken

    credentials = google.oauth2.credentials.Credentials(google_access_token)
    authed_session = AuthorizedSession(credentials)

    try:
        response_google = authed_session.get('https://www.googleapis.com/oauth2/v2/userinfo')

        user_data = response_google.content.decode('utf-8')
        user_data = json.loads(user_data)
        user_email = user_data['email']

        # access token으로 사용자의 이메일 주소를 알아낸뒤 user_info.json에 해당 사용자의 이메일 정보 추가
        with open('./user_info.json', 'r') as f:
            user_info = json.load(f)
            for i, each_user_info in enumerate(user_info):
                if each_user_info['accessToken'] == accessToken:
                    temp = {}
                    temp['accessToken'] = accessToken
                    temp['before_action'] = action_name
                    temp['selected_recipe'] = selected_recipe
                    temp['recipe_step'] = current_recipe_step
                    temp['user_email'] = user_email
                    user_info[i] = temp
                    break

        with open('./user_info.json', 'w', encoding='utf-8') as f:
            json.dump(user_info, f, ensure_ascii=False, indent=4)


    # access token이 만기되면 user_info.json에 저장되어 있던 사용자의 이메일 사용
    except:
        with open('./user_info.json', 'r') as f:
            user_info = json.load(f)
            for each_user_info in user_info:
                if each_user_info['accessToken'] == accessToken:
                    user_email = each_user_info['user_email']
                    break


    # SMTP 세션 생성
    google_server = smtplib.SMTP('smtp.gmail.com', 587)
    # 서버 연결 설정 (SMTP 통신 시작)
    google_server.ehlo()
    # 연결 암호화 (TLS 설정)
    google_server.starttls()
    # GMAIL 로그인 인증
    google_server.login('rladuddls9390@gmail.com', 'wtpx ksqx seof xuii')


    email_content = '요리 이름 : ' + selected_recipe['food_name']
    email_content += '\n\n요리 재료 : ' + selected_recipe['ingredients']
    email_content += '\n\n요리 예상 시간 : ' + selected_recipe['cook_time']
    email_content += '\n\n요리 레시피 : '
    for step in selected_recipe['recipe']:
        email_content += step + '\n'

    msg = MIMEText(email_content)
    msg['Subject'] = '요청하신 "' + selected_recipe['food_name'] + '" 요리 정보 입니다.'
    msg['From'] = 'rladuddls9390@gmail.com'
    msg['To'] = user_email

    google_server.sendmail('rladuddls9390@gmail.com', user_email, msg.as_string())
    google_server.quit()


def enable_music_play(response):
    AudioPlayer = {}
    AudioPlayer['type'] = 'AudioPlayer.Play'

    audioItem = {}
    stream = {}


    rand_num = random.randrange(1, 14)

    stream['url'] = 'http://163.239.169.54:5001/stream/music1.mp3'
    # 노래 재생 시작지점 '0'이면 처음부터
    stream['offsetInMilliseconds'] = 0

    '''
    progressReport = {}
    progressReport['progressReportDelayInMilliseconds'] = 0
    progressReport['progressReportIntervalInMilliseconds'] = 0
    stream['progressReport'] = progressReport
    '''
    stream['progressReport'] = None

    stream['token'] = 'something'
    stream['expectedPreviousToken'] = 'something'

    audioItem['stream'] = stream
    audioItem['metadata'] = None

    AudioPlayer['audioItem'] = audioItem

    response['directives'] = [AudioPlayer]

    return response

# ======================================================================================================================


@app.route('/answer.ask_recipe', methods=['POST'])
def ask_recipe():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    action_name = req['action']['actionName']
    try:
        accessToken = req['context']['session']['accessToken']
    # nugu builder에서 test하는 경우 accessToken을 'dev'로 설정
    except:
        accessToken = 'dev'


    check_user(accessToken)

    # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
    update_user_info_json_file(accessToken, action_name, 0, None)


    output = {}
    output['fulfillment_ask_recipe'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주시고, "한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'

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
    check_user(accessToken)

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    # 한식, 중식, 일식, 양식, 분식
    food_type = parameters['food_type']['value']

    with open('./recipes.json', 'r') as f:
        recipes = json.load(f)
        for i in recipes:
            # 사용자가 선택한 food type 찾는다
            if i['food_type'] == food_type:
                rand_num = random.randrange(0, 2)
                # 랜덤 추천된 레시피 정보
                selected_recipe = i['foods'][rand_num]
                break


    # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
    update_user_info_json_file(accessToken, action_name, 0, selected_recipe)


    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    output['fulfillment_food_type'] = food_type
    output['fulfillment_food_name'] = selected_recipe['food_name']

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)



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

    check_user(accessToken)


    with open('./user_info.json', 'r') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                current_recipe_step = each_user_info['recipe_step']
                selected_recipe = each_user_info['selected_recipe']



    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    # 레시피 설명 시작 전
    if current_recipe_step == 0:
        output['fulfillment_ask_ingredients'] = selected_recipe['ingredients'] + ' 이 필요합니다.'
        output['fulfillment_ask_ingredients'] += ' 레시피 상세 안내를 이메일로도 전송해 드릴 수 있어요. 이메일로 받아보시려면 누구앱에서 구글 계정을 연동하세요.'
        output['fulfillment_ask_ingredients'] += ' 이메일로 받아보시겠어요? "응" 또는 "아니" 로 말씀해주세요.'

        # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
        update_user_info_json_file(accessToken, action_name, 0, selected_recipe)
    # 레시피 설명 도중
    else:
        output['fulfillment_ask_ingredients'] = selected_recipe['ingredients'] + ' 입니다.'
        output['fulfillment_ask_ingredients'] += ' 현재 단계를 다시 들으시려면 "아리아, [요리왕]에서 방금 안내 다시 들려줘" 라고 이야기 해 주시고,'
        output['fulfillment_ask_ingredients'] += ' 다음 단계로 넘어가시려면 "아리아, [요리왕]에서 다음 안내 들려줘" 라고 이야기 해 주세요.'

        update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe)


    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)




@app.route('/answer.start_recipe', methods=['POST'])
def start_recipe():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    #print(req)
    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken)

    
    # 첫번째 step 이기때문에 1로 고정 설정
    current_recipe_step = 1

    with open('./user_info.json', 'r') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                selected_recipe = each_user_info['selected_recipe']


    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    # 첫번째 레시피 step 알림
    output['fulfillment_start_recipe'] = selected_recipe['recipe'][current_recipe_step] + ' 다 되시면 ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'

    # 다음 단계로 넘어가니까 step + 1
    update_user_info_json_file(accessToken, action_name, current_recipe_step + 1, selected_recipe)


    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
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

    check_user(accessToken)

    with open('./user_info.json', 'r') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                current_recipe_step = each_user_info['recipe_step']
                selected_recipe = each_user_info['selected_recipe']


    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    try:
        output['fulfillment_next'] = selected_recipe['recipe'][current_recipe_step]
    # list index out of range
    except IndexError:
        output['fulfillment_next'] = ''

    # step 1 증가 후 user_info.json에 입력
    update_user_info_json_file(accessToken, action_name, current_recipe_step + 1, selected_recipe)

    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    # 마지막 recipe step 이라면
    if current_recipe_step + 1 >= len(selected_recipe['recipe']):
        output['fulfillment_next'] += ' 이것이 요리의 마지막 안내입니다. 다시들으시려면 "아리아, [요리왕] 처음부터 안내" 라고 말해주세요. 저는 안내를 종료하겠습니다. 다음에 또 이용해주세요.'
    else:
        output['fulfillment_next'] += ' 다 되시면 ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None


    return jsonify(response)


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

    check_user(accessToken)



    with open('./user_info.json', 'r') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                current_recipe_step = each_user_info['recipe_step']
                selected_recipe = each_user_info['selected_recipe']


    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe)

    # 방금 전 단계를 가리키기 위해 -1
    current_recipe_step -= 1

    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    try:
        output['fulfillment_repeat'] = selected_recipe['recipe'][current_recipe_step] + ' 다 되시면 ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'
    except IndexError:
        output['fulfillment_repeat'] = '이것이 요리의 마지막 안내입니다. 다시들으시려면 "아리아, [요리왕] 처음부터 안내" 라고 말해주세요. 저는 안내를 종료하겠습니다. 다음에 또 이용해주세요.'


    response['version'] = '2.0'
    response['resultCode'] = 'OK'
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

    check_user(accessToken)

    with open('./user_info.json', 'r') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                current_recipe_step = each_user_info['recipe_step']
                selected_recipe = each_user_info['selected_recipe']

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    # 레시피 설명하기 전 처음으로 가고자 할 경우
    if current_recipe_step == 0:
        output['fulfillment_start'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, selected_recipe)
    # 레시피 설명 도중 처음으로 가고자 할 경우
    else:
        output['fulfillment_start'] = '다른 레시피를 추천해드릴까요? "응" 또는 "아니" 로 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe)



    response['version'] = '2.0'
    response['resultCode'] = 'OK'
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

    check_user(accessToken)

    with open('./user_info.json', 'r') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                # confirm_yes intent로 들어오기 전에 무슨 action이었는지 확인
                before_action = each_user_info['before_action']
                current_recipe_step = each_user_info['recipe_step']
                selected_recipe = each_user_info['selected_recipe']

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    if before_action == 'answer.start':
        output['fulfillment_confirm_yes'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주시고, "한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
    # 이메일 전송할 경우
    elif before_action == 'answer.ask_ingredients':
        # nugu builder 사용 혹은 계정 미연동
        if accessToken == 'dev':
            output['fulfillment_confirm_yes'] = 'NUGU builder로 테스트 하시거나, NUGU 앱에서 계정 연동을 하지 않으시면 이메일 발송이 불가능합니다.'
            output['fulfillment_confirm_yes'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
        # nugu app에서 계정 연동
        else:
            send_gmail_to_user(accessToken, selected_recipe, action_name, current_recipe_step)
            output['fulfillment_confirm_yes'] = '레시피를 이메일로 발송하였습니다. 수신함을 확인해 보세요.'
            output['fulfillment_confirm_yes'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'


    update_user_info_json_file(accessToken, action_name, 0, selected_recipe)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
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

    check_user(accessToken)

    with open('./user_info.json', 'r') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                # confirm_no intent로 들어오기 전에 무슨 action이었는지 확인
                before_action = each_user_info['before_action']
                selected_recipe = each_user_info['selected_recipe']


    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    if before_action == 'answer.start':
        output['fulfillment_confirm_no'] = '그럼 현재 레시피를 처음 단계부터 다시 알려드릴게요.'
        output['fulfillment_confirm_no'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
    # 이메일 전송 안하는 경우
    elif before_action == 'answer.ask_ingredients':
        output['fulfillment_confirm_no'] = '그럼 바로 레시피 안내를 시작할까요? 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'


    update_user_info_json_file(accessToken, action_name, 0, selected_recipe)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.send_email', methods=['POST'])
def send_email():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))
    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken)

    with open('./user_info.json', 'r') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                current_recipe_step = each_user_info['recipe_step']
                selected_recipe = each_user_info['selected_recipe']

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    # nugu builder 사용 혹은 계정 미연동
    if accessToken == 'dev':
        output['fulfillment_send_email'] = 'NUGU builder를 사용하시거나, NUGU 앱에서 계정 연동을 하지 않으시면 이메일 발송이 불가능합니다.'
        # 레시피 설명 전
        if current_recipe_step == 0:
            output['fulfillment_send_email'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
        # 레시피 설명 중
        else:
            output['fulfillment_send_email'] += ' 레시피를 이어서 들으시려면 "다음안내 들려줘" 라고 말씀해주세요.'
    # nugu app에서 계정 연동
    else:
        send_gmail_to_user(accessToken, selected_recipe, action_name, current_recipe_step)
        # 레시피 설명하기 전
        if current_recipe_step == 0:
            output['fulfillment_send_email'] = '레시피를 이메일로 발송하였습니다. 수신함을 확인해보세요. 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
            update_user_info_json_file(accessToken, action_name, 0, selected_recipe)
        # 레시피 설명중
        else:
            output['fulfillment_send_email'] = '레시피를 이메일로 발송하였습니다. 수신함을 확인해보세요. 레시피를 이어서 들으시려면 "다음안내 들려줘" 라고 말씀해주세요.'
            update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe)




    response['version'] = '2.0'
    response['resultCode'] = 'OK'
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