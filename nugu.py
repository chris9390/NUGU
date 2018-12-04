from flask import Flask, request, jsonify, send_from_directory
import os
import json
import requests
import random
import google.oauth2.credentials
from google.auth.transport.requests import AuthorizedSession
import smtplib
from email.mime.text import MIMEText
import urllib.parse
import threading

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




# ======================================================================================================================
# 다양한 다음 단계 설명 유도 문장들
next_step_invoke = ['아리아, [요리왕]에서 "다음 안내 들려줘"',
                    '아리아, [요리왕]에서 "다음 순서 알려줘"',
                    '아리아, [요리왕]에서 "다음엔 뭘 하면 될까?"',
                    '아리아, [요리왕]에서 "다음에 뭐해?"']

# 다양한 이전 단계 설명 유도 문장들
prev_step_invoke = ['아리아, [요리왕]에서 "전 단계 알려줘"',
                    '아리아, [요리왕]에서 "전 순서 알려줘"']



# 새로운 사용자인지 확인. 새로운 사용자면 info_user.json에 등록
def check_user(accessToken):
    is_new_user = 1
    is_exist_access_token = 0

    # access token 테스트 용 코드
    a, b = get_user_email(accessToken)
    # access token 테스트 용 코드

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                is_exist_access_token = 1
                break
            else:
                is_exist_access_token = 0

    # 기존에 user_info.json에 등록되지 않은 access token 이라면  "1. 새로운 사용자" (또는) "2. 기존 사용자의 access token 만료" 두가지 경우
    if is_exist_access_token == 0:
        user_email, is_saved_token = get_user_email(accessToken)
        for i, each_user_info in enumerate(user_info):

            if each_user_info['accessToken'] == 'dev':
                continue

            # 기존에 등록되어 있던 이메일 이면 기존 사용자
            if each_user_info['user_email'] == user_email:
                # 기존에 등록되어 있던 사용자의 access token refresh
                user_info[i]['accessToken'] = accessToken
                # user_info.json 파일 업데이트
                with open('./user_info.json', 'w', encoding='utf-8') as f:
                    json.dump(user_info, f, ensure_ascii=False, indent=4, sort_keys=True)
                is_new_user = 0
                break
            else:
                is_new_user = 1

        # 새로운 사용자인 경우
        if is_new_user == 1:
            new_user = {}
            new_user['accessToken'] = accessToken
            new_user['user_email'] = user_email

            # 계정 연동하고, 사용자 등록 안된 채로 1시간이 지나서 access token이 만기된 경우
            if is_saved_token == 0:
                new_user['need_oauth_reconnect'] = 1
            else:
                new_user['need_oauth_reconnect'] = 0

            # "요리왕" 실행 횟수
            new_user['run_count'] = 0

            # 고급 사용자 모드 설정
            new_user['skip_mode'] = 0


            # 새로운 사용자를 user_info 리스트에 추가
            user_info.append(new_user)
            # 그리고 user_info.json 파일 업데이트
            with open('./user_info.json', 'w', encoding='utf-8') as f:
                json.dump(user_info, f, ensure_ascii=False, indent=4, sort_keys=True)


# 사용자 정보 업데이트
def update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode):

    user_email = None

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                user_email = each_user_info['user_email']
                run_count = each_user_info['run_count']



    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        # 사용자 리스트 루프 돌면서
        for i, each_user_info in enumerate(user_info):
            # 해당 사용자 찾는다
            if each_user_info['accessToken'] == accessToken:
                temp = {}
                temp['accessToken'] = accessToken
                temp['before_action'] = action_name

                if action_name == 'answer.inform_food_type':
                    temp['run_count'] = run_count + 1
                else:
                    temp['run_count'] = run_count


                # 1이면 모드 설정, 0이면 아님
                temp['skip_mode'] = skip_mode

                try:
                    # 전 전 action
                    temp['bef_bef_action'] = each_user_info['before_action']
                except:
                    temp['bef_bef_action'] = ''
                temp['selected_recipe'] = selected_recipe
                temp['recipe_step'] = current_recipe_step
                temp['user_email'] = user_email
                temp['need_oauth_reconnect'] = each_user_info['need_oauth_reconnect']
                # 해당 사용자 정보 갱신
                user_info[i] = temp
                break


    # 사용자의 accessToken과 레시피 step을 user_info.json 파일에 저장.
    with open('./user_info.json', 'w', encoding='utf-8') as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4, sort_keys=True)



def get_user_email(accessToken):

    # accessToken이 user_info에 저장 되었는지 유무
    is_saved_token = 0

    # UnboundLocalError에 따른 선언 추가
    user_email = None

    if accessToken == 'dev':
        user_email = None
        return user_email, 1


    try:
        google_access_token = accessToken
        credentials = google.oauth2.credentials.Credentials(google_access_token)
        authed_session = AuthorizedSession(credentials)
        response_google = authed_session.get('https://www.googleapis.com/oauth2/v2/userinfo')
        user_data = response_google.content.decode('utf-8')
        user_data = json.loads(user_data)
        user_email = user_data['email']
        print('access token not expired')
        is_saved_token = 1
    # accessToken이 만기가 되었으면..
    except Exception as e:
        print('access token expired')
        print('\nException at (get_user_email) : ' + str(e) + '\n')
        with open('./user_info.json', 'r', encoding='utf-8') as f:
            user_info = json.load(f)
            for each_user_info in user_info:
                if each_user_info['accessToken'] == accessToken:
                    user_email = each_user_info['user_email']
                    is_saved_token = 1

    return user_email, is_saved_token


def send_gmail_to_user(accessToken, selected_recipe, action_name, current_recipe_step, run_count, skip_mode):

    try:
        google_access_token = accessToken
        credentials = google.oauth2.credentials.Credentials(google_access_token)
        authed_session = AuthorizedSession(credentials)
        response_google = authed_session.get('https://www.googleapis.com/oauth2/v2/userinfo')

        user_data = response_google.content.decode('utf-8')
        user_data = json.loads(user_data)
        user_email = user_data['email']

        # access token으로 사용자의 이메일 주소를 알아낸뒤 user_info.json에 해당 사용자의 이메일 정보 추가
        with open('./user_info.json', 'r', encoding='utf-8') as f:
            user_info = json.load(f)
            for i, each_user_info in enumerate(user_info):
                if each_user_info['accessToken'] == accessToken:
                    temp = {}
                    temp['accessToken'] = accessToken
                    temp['before_action'] = action_name
                    temp['selected_recipe'] = selected_recipe
                    temp['recipe_step'] = current_recipe_step
                    temp['user_email'] = user_email
                    temp['run_count'] = run_count
                    temp['skip_mode'] = skip_mode
                    temp['need_oauth_reconnect'] = 0
                    user_info[i] = temp
                    break

        with open('./user_info.json', 'w', encoding='utf-8') as f:
            json.dump(user_info, f, ensure_ascii=False, indent=4, sort_keys=True)


    # access token이 만기되면 user_info.json에 저장되어 있던 사용자의 이메일 사용
    except:
        with open('./user_info.json', 'r', encoding='utf-8') as f:
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


    recipe_steps = ''
    for step in selected_recipe['recipe']:
        if step == "":
            continue
        recipe_steps += step + '<br><br>'


    html_content = """
    <html>
        <head></head>
        <body>
            <b>요리 이름 :</b> {}
            <br><br>
            <b>요리 재료 :</b> {}
            <br><br>
            <b>요리 예상 시간 :</b> {}
            <br><br>
            <b>요리 레시피</b>
            <blockquote style="border:6px; border-style:solid; border-color:#adff3a; border-radius: 20px 20px 20px 20px; padding: 1em;">
            {}
            </blockquote>
            <br>
            <b>요리 이미지</b>
            <blockquote>
            <img src={}>
            </blockquote>
            <br><br>
            <b>보다 더 자세한 설명을 보고싶으시다면 ☞ {}</b>
        </body>
    </html>
    """.format(selected_recipe['food_name'], selected_recipe['ingredients'], selected_recipe['cook_time'], recipe_steps, selected_recipe['img_src'],selected_recipe['url'])

    msg = MIMEText(html_content, 'html')
    msg['Subject'] = '요청하신 "' + selected_recipe['food_name'] + '" 요리 정보 입니다.'
    msg['From'] = 'rladuddls9390@gmail.com'
    msg['To'] = user_email

    try:
        google_server.sendmail('rladuddls9390@gmail.com', user_email, msg.as_string())
        google_server.quit()
    except:
        print('\n메일 전송 오류\n')


def enable_music_play(response):
    AudioPlayer = {}
    AudioPlayer['type'] = 'AudioPlayer.Play'

    audioItem = {}
    stream = {}

    music_path = './music'
    music_list = os.listdir(music_path)
    rand_num = random.randrange(0, len(music_list))

    music_title = music_list[rand_num]
    encoded_music_title = urllib.parse.quote_plus(music_title)

    with open('./recently_played_music.json', 'w', encoding='utf-8') as f:
        # url에 입력하기 위해 변경했던 '_' 를 다시 공백으로 변경해준다
        music_title = music_title.replace('_', ' ')
        # .mp3 부분 제거
        music_title = music_title.replace('.mp3', '')
        music_info = {}
        music_info['music_title'] = music_title
        json.dump(music_info, f, ensure_ascii=False, indent=4, sort_keys=True)

    stream['url'] = 'http://163.239.169.54:5001/stream/' + encoded_music_title
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


    import datetime
    print('\ncurrent time : ' + str(datetime.datetime.now()))
    print('access token : ' + accessToken + '\n')


    check_user(accessToken)

    output = {}
    output['fulfillment_ask_recipe'] = ''

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                run_count = each_user_info['run_count']
                # 3번 이상 사용했으면
                if run_count >= 3:
                    output['fulfillment_ask_recipe'] = '요리왕을 세번 이상 사용하셨네요! 자세한 사용법 설명이 생략되는 고급 사용자 모드로 전환할까요? 응, 해줘 또는 아니, 괜찮아 로 말씀해주세요.'
                    update_user_info_json_file(accessToken, action_name, 0, None, 0)
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)



    # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
    update_user_info_json_file(accessToken, action_name, 0, None, 0)

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


    if food_type == '아무거나':
        temp = ['한식', '중식', '일식', '양식', '분식']
        rand_num = random.randrange(0, len(temp))
        food_type = temp[rand_num]


    with open('./recipes.json', 'r', encoding='utf-8') as f:
        recipes = json.load(f)
        for i in recipes:
            # 사용자가 선택한 food type 찾는다
            if i['food_type'] == food_type:
                rand_num = random.randrange(0, 2)
                # 랜덤 추천된 레시피 정보
                selected_recipe = i['foods'][rand_num]
                break



    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_ask_ingredients'] = '"레시피 추천해줘" 라고 먼저 말씀해주세요.'

                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)

                break

    # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
    update_user_info_json_file(accessToken, action_name, 0, selected_recipe, skip_mode)


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
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    current_recipe_step = each_user_info['recipe_step']
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_ask_ingredients'] = '"레시피 추천해줘" 라고 먼저 말씀해주세요.'

                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)

                break





    # 레시피 설명 시작 전
    if current_recipe_step == 0:
        output['fulfillment_ask_ingredients'] = selected_recipe['ingredients'] + ' 이 필요합니다.'
        if accessToken == 'dev':
            output['fulfillment_ask_ingredients'] += ' 레시피 상세 안내를 이메일 로도 전송해 드릴 수도 있어요. 이메일로 받아보시려면 NUGU 앱에서 구글 계정을 연동하세요.'
            output['fulfillment_ask_ingredients'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악이 재생되고 있는 중에 [요리왕]에 다른 명령을 하고 싶으시면, 먼저 "아리아, 종료" 혹은 "아리아, 그만" 같이 말씀하셔서 음악을 중지시킨 후에 말씀해주세요.'
            output['fulfillment_ask_ingredients'] += ' 레시피 안내를 시작하시려면, "레시피 시작" 이라고 이야기 해 주세요.'
        else:
            output['fulfillment_ask_ingredients'] += ' 레시피 상세 안내를 이메일 로도 전송해 드릴 수 있어요. 이메일로 받아보시겠어요? "응 해줘" 또는 "아니 괜찮아" 로 말씀해주세요.'

        # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
        update_user_info_json_file(accessToken, action_name, 0, selected_recipe, skip_mode)
    # 레시피 설명 도중
    else:
        output['fulfillment_ask_ingredients'] = selected_recipe['ingredients'] + ' 입니다.'
        output['fulfillment_ask_ingredients'] += ' 방금 단계를 다시 들으시려면 "아리아, [요리왕]에서 방금 안내 다시 들려줘" 라고 이야기 해 주시고,'
        output['fulfillment_ask_ingredients'] += ' 다음 단계로 넘어가시려면 "아리아, [요리왕]에서 다음 안내 들려줘" 라고 이야기 해 주세요.'

        update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)


    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)




@app.route('/answer.start_recipe', methods=['POST'])
def start_recipe():
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

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']
    
    # 첫번째 step 이기때문에 1로 고정 설정
    current_recipe_step = 1

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_start_recipe'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'

                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)
                break




    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    # 첫번째 레시피 step 알림
    output['fulfillment_start_recipe'] = selected_recipe['recipe'][current_recipe_step] + ' 다 되시면 먼저 노래를 종료한 뒤에, ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'


    update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)

    # 랜덤 음악 재생
    enable_music_play(response)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    #response['directives'] = None

    return jsonify(response)



@app.route('/answer.next', methods=['POST'])
def next():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        # OAuth 를 사용하지 않는 경우
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    current_recipe_step = each_user_info['recipe_step']
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_next'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'

                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)

                break


    # 아직 마지막 단계가 아니라면 한 단계 증가
    if current_recipe_step != len(selected_recipe['recipe'])-1:
        current_recipe_step += 1


    try:
        output['fulfillment_next'] = selected_recipe['recipe'][current_recipe_step]
    # list index out of range
    except IndexError:
        output['fulfillment_next'] = ''




    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    # 마지막 recipe step 이라면
    if current_recipe_step >= len(selected_recipe['recipe'])-1:
        output['fulfillment_next'] += ' 이것이 요리의 마지막 안내입니다. 다시들으시려면 "아리아, [요리왕]에서 처음부터 안내" 라고 말해주세요. 저는 안내를 종료하겠습니다. 다음에 또 이용해주세요.'
    else:
        output['fulfillment_next'] += ' 다 되시면 먼저 노래를 종료한 뒤에, ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'
        # 랜덤 음악 재생
        enable_music_play(response)

    update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    #response['directives'] = None


    return jsonify(response)


@app.route('/answer.prev', methods=['POST'])
def prev():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        # OAuth 를 사용하지 않는 경우
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    current_recipe_step = each_user_info['recipe_step']
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_prev'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)
                break

    # 한 단계 감소
    current_recipe_step -= 1



    try:
        output['fulfillment_prev'] = selected_recipe['recipe'][current_recipe_step]
    # list index out of range
    except IndexError:
        output['fulfillment_prev'] = ''




    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(prev_step_invoke))

    # 첫 번째 step 전으로 가려고 하면
    if current_recipe_step <= 0:
        output['fulfillment_prev'] += '이미 첫번째 단계입니다. ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'
        update_user_info_json_file(accessToken, action_name, 1, selected_recipe, skip_mode)
    else:
        output['fulfillment_prev'] += ' 다 되시면 먼저 노래를 종료한 뒤에, ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'
        # 랜덤 음악 재생
        enable_music_play(response)
        update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)



    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    #response['directives'] = None


    return jsonify(response)



@app.route('/answer.repeat', methods=['POST'])
def repeat():
    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        # OAuth 를 사용하지 않는 경우
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    current_recipe_step = each_user_info['recipe_step']
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_repeat'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    # response['directives'] = None

                    return jsonify(response)
                break





    update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)


    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    try:
        output['fulfillment_repeat'] = selected_recipe['recipe'][current_recipe_step] + ' 다 되시면 먼저 노래를 종료한 뒤에, ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'
        # 랜덤 음악 재생
        enable_music_play(response)
    except IndexError:
        output['fulfillment_repeat'] = '이것이 요리의 마지막 안내입니다. 다시 들으시려면 "아리아, [요리왕]에서 처음부터 안내" 라고 말해주세요. 저는 안내를 종료하겠습니다. 다음에 또 이용해주세요.'


    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    #response['directives'] = None

    return jsonify(response)


@app.route('/answer.start', methods=['POST'])
def start():
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

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    current_recipe_step = each_user_info['recipe_step']
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_start'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)
                break



    # 레시피 설명하기 전 처음으로 가고자 할 경우
    if current_recipe_step == 0:
        output['fulfillment_start'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, selected_recipe, skip_mode)
    # 레시피 설명 도중 처음으로 가고자 할 경우
    else:
        output['fulfillment_start'] = '다른 레시피를 추천해드릴까요? "응 해줘" 또는 "아니 괜찮아" 로 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)



    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.confirm_yes', methods=['POST'])
def confirm_yes():
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

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    need_oauth_reconnect = 0

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    # confirm_yes intent로 들어오기 전에 무슨 action이었는지 확인
                    before_action = each_user_info['before_action']
                    current_recipe_step = each_user_info['recipe_step']
                    selected_recipe = each_user_info['selected_recipe']
                    need_oauth_reconnect = each_user_info['need_oauth_reconnect']
                    run_count = each_user_info['run_count']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_confirm_yes'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)
                break




    if before_action == 'answer.start':
        output['fulfillment_confirm_yes'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주시고, "한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, selected_recipe, skip_mode)
    # 이메일 전송할 경우
    elif before_action == 'answer.ask_ingredients':
        # nugu builder 사용 혹은 계정 미연동
        if accessToken == 'dev':
            output['fulfillment_confirm_yes'] = 'NUGU builder로 테스트 하시거나, NUGU 앱에서 계정 연동을 하지 않으시면 이메일 발송이 불가능합니다.'
            output['fulfillment_confirm_yes'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악이 재생되고 있는 중에 [요리왕]에 다른 명령을 하고 싶으시면, 먼저 "아리아, 종료" 혹은 "아리아, 그만" 같이 말씀하셔서 음악을 중지시킨 후에 말씀해주세요.'
            output['fulfillment_confirm_yes'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'

        # 계정 연동 해제 후 다시 연결해야 하는 경우
        elif need_oauth_reconnect == 1:
            output['fulfillment_confirm_yes'] = '이메일 발송을 원하시면 NUGU 앱에서 계정 연동을 해제하시고, 다시 연결해주세요.'
            output['fulfillment_confirm_yes'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악이 재생되고 있는 중에 [요리왕]에 다른 명령을 하고 싶으시면, 먼저 "아리아, 종료" 혹은 "아리아, 그만" 같이 말씀하셔서 음악을 중지시킨 후에 말씀해주세요.'
            output['fulfillment_confirm_yes'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'

        # nugu app에서 계정 연동
        else:
            t = threading.Thread(target=send_gmail_to_user, args=(accessToken, selected_recipe, action_name, current_recipe_step, run_count, skip_mode))
            t.start()
            #send_gmail_to_user(accessToken, selected_recipe, action_name, current_recipe_step)
            output['fulfillment_confirm_yes'] = '레시피를 이메일로 발송하였습니다. 수신함을 확인해 보세요.'
            output['fulfillment_confirm_yes'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악이 재생되고 있는 중에 [요리왕]에 다른 명령을 하고 싶으시면, 먼저 "아리아, 종료" 혹은 "아리아, 그만" 같이 말씀하셔서 음악을 중지시킨 후에 말씀해주세요.'
            output['fulfillment_confirm_yes'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'

        update_user_info_json_file(accessToken, action_name, 0, selected_recipe, skip_mode)

    elif before_action == 'answer.ask_recipe':
        output['fulfillment_confirm_yes'] = '고급 사용자 모드로 전환되었습니다. 한식, 중식, 일식, 양식, 분식 중에 선택해주시고, "한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, selected_recipe, 1)



    #update_user_info_json_file(accessToken, action_name, 0, selected_recipe, 0)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.confirm_no', methods=['POST'])
def confirm_no():
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

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    # confirm_no intent로 들어오기 전에 무슨 action이었는지 확인
                    before_action = each_user_info['before_action']
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_confirm_no'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)
                break





    if before_action == 'answer.start':
        output['fulfillment_confirm_no'] = '그럼 현재 레시피를 처음 단계부터 다시 알려드릴게요.'
        output['fulfillment_confirm_no'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, selected_recipe, skip_mode)
    # 이메일 전송 안하는 경우
    elif before_action == 'answer.ask_ingredients':
        output['fulfillment_confirm_no'] = '그럼 바로 레시피 안내를 시작할게요.'
        output['fulfillment_confirm_no'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악이 재생되고 있는 중에 [요리왕]에 다른 명령을 하고 싶으시면, 먼저 "아리아, 종료" 혹은 "아리아, 그만" 같이 말씀하셔서 음악을 중지시킨 후에 말씀해주세요.'
        output['fulfillment_confirm_no'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, selected_recipe, skip_mode)
    elif before_action == 'answer.ask_recipe':
        output['fulfillment_confirm_no'] = '네, 그럼 원래대로 설명드리겠습니다. 한식, 중식, 일식, 양식, 분식 중에 선택해주시고, "한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, selected_recipe, 0)




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

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    need_oauth_reconnect = 0

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    current_recipe_step = each_user_info['recipe_step']
                    selected_recipe = each_user_info['selected_recipe']
                    need_oauth_reconnect = each_user_info['need_oauth_reconnect']
                    run_count = each_user_info['run_count']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_send_email'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)
                break




    # nugu builder 사용 혹은 계정 미연동
    if accessToken == 'dev':
        output['fulfillment_send_email'] = 'NUGU builder를 사용하시거나, NUGU 앱에서 계정 연동을 하지 않으시면 이메일 발송이 불가능합니다.'
        output['fulfillment_send_email'] += ' 이메일로 레시피를 받아보시려면, NUGU 앱에서 계정 연동을 하시고 다시 시도해주세요.'
        # 레시피 설명 전
        if current_recipe_step == 0:
            output['fulfillment_send_email'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악이 재생되고 있는 중에 [요리왕]에 다른 명령을 하고 싶으시면, 먼저 "아리아, 종료" 혹은 "아리아, 그만" 같이 말씀하셔서 음악을 중지시킨 후에 말씀해주세요.'
            output['fulfillment_send_email'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
        # 레시피 설명 중
        else:
            output['fulfillment_send_email'] += ' 레시피를 이어서 들으시려면 "다음안내 들려줘" 라고 말씀해주세요.'

    # 계정 연동 해제 후 다시 연결해야 하는 경우
    elif need_oauth_reconnect == 1:
        output['fulfillment_send_email'] = '이메일 발송을 원하시면 NUGU 앱에서 계정 연동을 해제하시고, 다시 연결해주세요.'
        output['fulfillment_send_email'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악이 재생되고 있는 중에 [요리왕]에 다른 명령을 하고 싶으시면, 먼저 "아리아, 종료" 혹은 "아리아, 그만" 같이 말씀하셔서 음악을 중지시킨 후에 말씀해주세요.'
        output['fulfillment_send_email'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'

    # nugu app에서 계정 연동
    else:
        t = threading.Thread(target=send_gmail_to_user,args=(accessToken, selected_recipe, action_name, current_recipe_step, run_count, skip_mode))
        t.start()
        #send_gmail_to_user(accessToken, selected_recipe, action_name, current_recipe_step)
        # 레시피 설명하기 전
        if current_recipe_step == 0:
            output['fulfillment_send_email'] = '레시피를 이메일로 발송하였습니다. 수신함을 확인해보세요.'
            output['fulfillment_send_email'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악이 재생되고 있는 중에 [요리왕]에 다른 명령을 하고 싶으시면, 먼저 "아리아, 종료" 혹은 "아리아, 그만" 같이 말씀하셔서 음악을 중지시킨 후에 말씀해주세요.'
            output['fulfillment_send_email'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
            update_user_info_json_file(accessToken, action_name, 0, selected_recipe, skip_mode)
        # 레시피 설명중
        else:
            output['fulfillment_send_email'] = '레시피를 이메일로 발송하였습니다. 수신함을 확인해보세요. 레시피를 이어서 들으시려면 "다음안내 들려줘" 라고 말씀해주세요.'
            update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)




    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.ask_music', methods=['POST'])
def ask_music():
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

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    # confirm_no intent로 들어오기 전에 무슨 action이었는지 확인
                    before_action = each_user_info['before_action']
                    selected_recipe = each_user_info['selected_recipe']
                    current_recipe_step = each_user_info['recipe_step']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_ask_music'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)
                break



    with open('./recently_played_music.json', 'r', encoding='utf-8') as f:
        music_info = json.load(f)
        music_title = music_info['music_title']


    output['fulfillment_ask_music'] = '방금 재생된 음악은 ' + music_title + ' 입니다.'
    output['fulfillment_ask_music'] += ' 다음 단계로 넘어가시려면 "아리아, [요리왕]에서 다음 안내 들려줘" 라고 이야기 해 주세요.'

    update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)



@app.route('/answer.ask_food_name', methods=['POST'])
def ask_food_name():
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

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    selected_recipe = each_user_info['selected_recipe']
                    current_recipe_step = each_user_info['recipe_step']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_ask_food_name'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)
                break




    output['fulfillment_ask_food_name'] = '지금 만들고 계신 요리는 ' + selected_recipe['food_name'] + ' 입니다.'


    update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.help', methods=['POST'])
def help():
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

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    selected_recipe = each_user_info['selected_recipe']
                    current_recipe_step = each_user_info['recipe_step']
                    # 전 action
                    before_action = each_user_info['before_action']
                    # 전 전 action
                    bef_bef_action = each_user_info['bef_bef_action']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_help'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    return jsonify(response)
                break




    if before_action == 'answer.ask_recipe':
        output['fulfillment_help'] = '"한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
    elif before_action == 'answer.inform_food_type':
        output['fulfillment_help'] = '"재료 안내해줘" 라고 이야기 해 보세요.'
    elif before_action == 'answer.ask_ingredients' and bef_bef_action == 'answer.inform_food_type':
        output['fulfillment_help'] = '"응, 해줘" 또는 "아니야, 괜찮아" 라고 이야기 해 보세요.'
    elif before_action == 'answer.ask_ingredients' and (bef_bef_action == 'answer.start_recipe' or bef_bef_action == 'answer.next' or bef_bef_action == 'answer.repeat'):
        output['fulfillment_help'] = '방금 단계를 다시 들으시려면 "아리아, [요리왕] 에서 방금 안내 다시 들려줘" 라고 이야기 해 주시고, 다음 단계로 넘어가시려면 "아리아, [요리왕] 에서 다음 안내 들려줘" 라고 이야기 해 주세요.'
    elif before_action == 'answer.start_recipe' or before_action == 'answer.next' or before_action == 'answer.repeat' or before_action == 'answer.prev':
        output['fulfillment_help'] = '"아리아, 요리왕에서 다음안내 들려줘" 라고 이야기 해보세요. 재료설명을 듣고 싶으시면 "아리아, 요리왕에서 재료 안내해줘" 라고 이야기 해보세요.'
    elif before_action == 'answer.start' and current_recipe_step == 0:
        output['fulfillment_help'] = '"한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
    elif before_action == 'answer.start' and current_recipe_step > 0:
        output['fulfillment_help'] = '"응, 해줘" 또는 "아니야, 괜찮아" 라고 이야기 해 보세요.'
    elif before_action == 'answer.confirm_yes' and bef_bef_action == 'answer.start':
        output['fulfillment_help'] = '"한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
    elif before_action == 'answer.confirm_yes' and bef_bef_action == 'answer.ask_ingredients':
        output['fulfillment_help'] = '"레시피 시작" 이라고 이야기 해 보세요.'
    elif before_action == 'answer.confirm_no' or before_action == 'answer.ask_food_name':
        output['fulfillment_help'] = '"레시피 시작" 이라고 이야기 해 보세요.'
    elif before_action == 'answer.send_email' or before_action == 'answer.ask_music':
        output['fulfillment_help'] = '"다음 안내 들려줘" 라고 이야기 해 보세요.'
    else:
        output['fulfillment_help'] = '"추천 레시피 알려줘" 라고 이야기 해 보세요.'



    update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    return jsonify(response)


@app.route('/answer.tutorial', methods=['POST'])
def tutorial():
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

    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    selected_recipe = each_user_info['selected_recipe']
                    current_recipe_step = each_user_info['recipe_step']
                    skip_mode = each_user_info['skip_mode']
                except:
                    selected_recipe = None
                    current_recipe_step = 0
                break

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    output['fulfillment_tutorial'] = '요리왕에서 할 수 있는 것을 알려드립니다. 처음부터 들으시려면 "처음부터 안내해줘"라고, 재료안내를 원하시면 "재료 안내해줘" 라고 말해보세요.'
    output['fulfillment_tutorial'] += ' 그 외, 부가기능도 있습니다.'
    output['fulfillment_tutorial'] += ' 이메일로 레시피를 받으시려면 "이메일로 레시피 보내줘", 노래 제목이 궁금하시면 "방금 재생된 음악 알려줘" 라고 말해보세요.'
    output['fulfillment_tutorial'] += ' 다시들으시려면 "사용법 알려줘"라고, 시작하시려면 "요리왕 시작해줘" 라고 말씀하세요.'


    update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode)

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
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)