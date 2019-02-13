from flask import Flask, request, jsonify, send_from_directory, g
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
import logging
import config
import pymysql
from db_helper import DB_Helper


app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'music'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER




@app.route('/stream/<filename>', methods=['GET'])
def stream(filename):
    print('root path : ' + app.root_path)
    uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    print('uploaded path : ' + str(uploads))
    print('filename : ' + filename)
    return send_from_directory(directory=uploads, filename=filename)




def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = pymysql.connect(host='163.239.169.54',
                             port=3306,
                             user='s20131533',
                             passwd='s20131533',
                             db='nugu_dm',
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)
        g._database = db
    else:
        db.ping()

    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



# ======================================================================================================================
# 다양한 다음 단계 설명 유도 문장들
next_step_invoke = ['아리아, 요리왕에서 "다음 안내 들려줘"',
                    '아리아, 요리왕에서 "다음 순서 알려줘"',
                    '아리아, 요리왕에서 "다음엔 뭘 하면 될까?"',
                    '아리아, 요리왕에서 "다음에 뭐해?"']

# 다양한 이전 단계 설명 유도 문장들
prev_step_invoke = ['아리아, 요리왕에서 "전 단계 알려줘"',
                    '아리아, 요리왕에서 "전 순서 알려줘"']


# 새로운 사용자인지 확인. 새로운 사용자면 info_user.json에 등록
def check_user(accessToken):
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    #is_new_user = 1
    #is_exist_access_token = 0

    user_email = ''


    # ============ DB로 다시 코딩하는 부분 ============== #

    existing_user = db_helper.select_by_token(accessToken)

    # 해당 accessToken 등록되지 않음
    if existing_user == None:
        is_exist_access_token = 0
    # access token이 등록된 사용자 이미 존재
    else:
        is_exist_access_token = 1
        user_email = existing_user['user_email']

    # DB에 등록되지 않은 access token 이라면
    # 1. 새로운 사용자.
    # 2. 기존 사용자의 access token 만료.
    if is_exist_access_token == 0:
        user_email, is_saved_token = get_user_email(accessToken)

        is_new_user = 1

        # 이메일로 사용자 검색
        existing_user_2 = db_helper.select_by_email(user_email)

        # 2. 인 경우 (이메일로 검색된 사용자가 있으면)
        if existing_user_2 != None:
            # 기존에 등록되어 있던 사용자의 accessToken refresh
            db_helper.update_user_info_table('accessToken', accessToken, 'user_email', user_email)
            is_new_user = 0

        # 1. 인 경우
        if is_new_user == 1:
            if is_saved_token == 0:
                db_helper.insert_new_user(accessToken, user_email, 1)
            else:
                db_helper.insert_new_user(accessToken, user_email, 0)

    # ============ DB로 다시 코딩하는 부분 ============== #


    '''
    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            # access token이 등록된 사용자 이미 존재
            if each_user_info['accessToken'] == accessToken:
                is_exist_access_token = 1
                user_email = each_user_info['user_email']
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
    '''


    if user_email == None:
        user_email = 'oauth_unconnected_users'


    mylogger = logging.getLogger(user_email)

    if len(mylogger.handlers) > 0:
        return mylogger

    mylogger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s | %(levelname)s] %(message)s')

    # 로그 파일의 이름을 사용자의 이메일로 설정
    logfilename = './logs/' + user_email + '.log'
    # filehandler 생성
    file_handler = logging.FileHandler(logfilename)
    # handler에 formatter 세팅
    file_handler.setFormatter(formatter)

    # handler를 logging에 추가
    mylogger.addHandler(file_handler)


    return mylogger





# 사용자 정보 업데이트
def update_user_info_json_file(accessToken, action_name, current_recipe_step, selected_recipe, skip_mode):
    user_email = None

    # ============ DB로 다시 코딩하는 부분 ============== #
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    existing_user = db_helper.select_by_token(accessToken)
    run_count = existing_user['run_count']

    db_helper.update_user_info_table('bef_bef_action', existing_user['before_action'], 'accessToken', accessToken)
    # db_helper.update_user_info_table_no_cond('bef_bef_action', existing_user['before_action'])

    db_helper.update_user_info_table('before_action', action_name, 'accessToken', accessToken)
    #db_helper.update_user_info_table_no_cond('before_action', action_name)

    if action_name == 'answer.inform_food_type':
        db_helper.update_user_info_table('run_count', run_count + 1, 'accessToken', accessToken)
        #db_helper.update_user_info_table_no_cond('run_count', run_count + 1)

    db_helper.update_user_info_table('skip_mode', skip_mode, 'accessToken', accessToken)
    #db_helper.update_user_info_table_no_cond('skip_mode', skip_mode)

    db_helper.update_user_info_table('selected_recipe', selected_recipe, 'accessToken', accessToken)
    #db_helper.update_user_info_table_no_cond('selected_recipe', selected_recipe)

    db_helper.update_user_info_table('recipe_step', current_recipe_step, 'accessToken', accessToken)
    #db_helper.update_user_info_table_no_cond('recipe_step', current_recipe_step)

    # ============ DB로 다시 코딩하는 부분 ============== #


    '''
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
    '''


def get_user_email(accessToken):
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

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
        print('access token not expired :)')
        is_saved_token = 1
    # accessToken이 만기가 되었으면..
    except Exception as e:
        print('access token expired :(')
        print('\nException at (get_user_email) : ' + str(e) + '\n')

        existing_user = db_helper.select_by_token(accessToken)
        if existing_user != None:
            user_email = existing_user['user_email']
            is_saved_token = 1

        '''
        with open('./user_info.json', 'r', encoding='utf-8') as f:
            user_info = json.load(f)
            for each_user_info in user_info:
                if each_user_info['accessToken'] == accessToken:
                    user_email = each_user_info['user_email']
                    is_saved_token = 1
        '''

    return user_email, is_saved_token


def send_gmail_to_user(accessToken, selected_recipe, action_name, current_recipe_step, run_count, skip_mode):
    #db_conn = get_db()
    #db_helper = DB_Helper(db_conn)

    db_conn = pymysql.connect(host='163.239.169.54',
                         port=3306,
                         user='s20131533',
                         passwd='s20131533',
                         db='nugu_dm',
                         charset='utf8',
                         cursorclass=pymysql.cursors.DictCursor)
    db_helper = DB_Helper(db_conn)

    try:
        google_access_token = accessToken
        credentials = google.oauth2.credentials.Credentials(google_access_token)
        authed_session = AuthorizedSession(credentials)
        response_google = authed_session.get('https://www.googleapis.com/oauth2/v2/userinfo')

        user_data = response_google.content.decode('utf-8')
        user_data = json.loads(user_data)
        user_email = user_data['email']


        # access token으로 사용자의 이메일 주소를 알아낸뒤 DB에 해당 사용자의 이메일 정보 업데이트
        db_helper.update_user_info_table('user_email', user_email, 'accessToken', accessToken)


        '''
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
        '''

    # access token이 만기되면 DB에 저장되어 있던 사용자의 이메일 사용
    except:
        existing_user = db_helper.select_by_token(accessToken)
        if existing_user != None:
            user_email = existing_user['user_email']

        '''
        with open('./user_info.json', 'r', encoding='utf-8') as f:
            user_info = json.load(f)
            for each_user_info in user_info:
                if each_user_info['accessToken'] == accessToken:
                    user_email = each_user_info['user_email']
                    break
        '''

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
    """.format(selected_recipe['food_name'], selected_recipe['ingredients'], selected_recipe['cook_time'], recipe_steps,
               selected_recipe['img_src'], selected_recipe['url'])

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

    #stream['url'] = 'http://163.239.169.54:5002/stream/' + encoded_music_title
    stream['url'] = 'http://' + str(config.IP) + ':' + str(config.PORT) + '/stream/' + encoded_music_title

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
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    # print(json.dumps(req, indent=4))

    action_name = req['action']['actionName']
    try:
        accessToken = req['context']['session']['accessToken']
    # nugu builder에서 test하는 경우 accessToken을 'dev'로 설정
    except:
        accessToken = 'dev'

    import datetime
    print('\ncurrent time : ' + str(datetime.datetime.now()))
    print('access token : ' + accessToken + '\n')

    mylogger = check_user(accessToken)


    output = {}
    output['fulfillment_ask_recipe'] = ''


    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        run_count = existing_user['run_count']
        # 3번 이상 사용했으면 고급 사용자 모드 트리거 (계정연동이 안되있는 경우는 제외)
        if run_count >= 3 and accessToken != 'dev':
            output['fulfillment_ask_recipe'] = '요리왕을 세번 이상 사용하셨네요! 자세한 사용법 설명이 생략되는, 고급 사용자 모드로 전환할까요? 응, 해줘 또는 아니, 괜찮아 로 말씀해주세요.'
            update_user_info_json_file(accessToken, action_name, 0, None, 0)
            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_recipe'])

            return jsonify(response)

    '''
    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                run_count = each_user_info['run_count']
                # 3번 이상 사용했으면 고급 사용자 모드 트리거 (계정연동이 안되있는 경우는 제외)
                if run_count >= 3 and accessToken != 'dev':
                    output['fulfillment_ask_recipe'] = '요리왕을 세번 이상 사용하셨네요! 자세한 사용법 설명이 생략되는, 고급 사용자 모드로 전환할까요? 응, 해줘 또는 아니, 괜찮아 로 말씀해주세요.'
                    update_user_info_json_file(accessToken, action_name, 0, None, 0)
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_recipe'])

                    return jsonify(response)
    '''

    # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
    update_user_info_json_file(accessToken, action_name, 0, None, 0)

    output['fulfillment_ask_recipe'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주시고, "한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None


    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_recipe'])

    return jsonify(response)


@app.route('/answer.inform_food_type', methods=['POST'])
def inform_food_type():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))
    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'

    # 동일한 사용자인지 확인
    mylogger = check_user(accessToken)

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
                rand_num = random.randrange(0, len(i['foods']))
                # 랜덤 추천된 레시피 정보(dict 타입)
                selected_recipe = i['foods'][rand_num]
                break

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        try:
            skip_mode = existing_user['skip_mode']
        except:
            output['fulfillment_inform_food_type'] = '"레시피 추천해줘" 라고 먼저 말씀해주세요.'

            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_inform_food_type'])

            return jsonify(response)

    '''
    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_inform_food_type'] = '"레시피 추천해줘" 라고 먼저 말씀해주세요.'

                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_inform_food_type'])

                    return jsonify(response)

                break
    '''


    # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
    update_user_info_json_file(accessToken, action_name, 0, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)


    output['fulfillment_inform_food_type'] = '오늘의 ' + food_type + '은 ' + selected_recipe['food_name'] + ' 입니다. 재료 안내를 원하시면 "재료 안내해줘" 라고 말씀해주세요.'

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_inform_food_type'])

    return jsonify(response)


@app.route('/answer.ask_ingredients', methods=['POST'])
def ask_ingredients():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        current_recipe_step = existing_user['recipe_step']

        if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
            output['fulfillment_ask_ingredients'] = '"레시피 추천해줘" 라고 먼저 말씀해주세요.'

            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info(
                'triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_ingredients'])

            return jsonify(response)
        else:
            selected_recipe = json.loads(existing_user['selected_recipe'])

        skip_mode = existing_user['skip_mode']


    '''
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

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_ingredients'])

                    return jsonify(response)

                break
    '''


    # 레시피 설명 시작 전
    if current_recipe_step == 0:
        output['fulfillment_ask_ingredients'] = selected_recipe['ingredients'] + ' 이 필요합니다.'
        if accessToken == 'dev':
            output['fulfillment_ask_ingredients'] += ' 레시피 상세 안내를 이메일 로도 전송해 드릴 수도 있어요. 이메일로 받아보시려면 NUGU 앱에서 구글 계정을 연동하세요.'
            output['fulfillment_ask_ingredients'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악 재생을 중지하고 싶으시면, "아리아, 종료" 혹은 "아리아, 그만" 이라고 말씀해주세요.'
            output['fulfillment_ask_ingredients'] += ' 레시피 안내를 시작하시려면, "레시피 시작" 이라고 이야기 해 주세요.'
        else:
            output['fulfillment_ask_ingredients'] += ' 레시피 상세 안내를 이메일 로도 전송해 드릴 수 있어요. 이메일로 받아보시겠어요? "응 해줘" 또는 "아니 괜찮아" 로 말씀해주세요.'

        # 레시피 안내 시작전이기 때문에 step은 0으로 초기 설정
        update_user_info_json_file(accessToken, action_name, 0, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)
    # 레시피 설명 도중
    else:
        output['fulfillment_ask_ingredients'] = selected_recipe['ingredients'] + ' 입니다.'
        output['fulfillment_ask_ingredients'] += ' 방금 단계를 다시 들으시려면 "방금 안내 한번더 들려줘" 라고 이야기 해 주시고,'
        output['fulfillment_ask_ingredients'] += ' 다음 단계로 넘어가시려면 "다음 안내 들려줘" 라고 이야기 해 주세요.'

        update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_ingredients'])

    return jsonify(response)


@app.route('/answer.start_recipe', methods=['POST'])
def start_recipe():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    # 첫번째 step 이기때문에 1로 고정 설정
    current_recipe_step = 1

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
            output['fulfillment_start_recipe'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'

            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info(
                'triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_start_recipe'])

            return jsonify(response)
        else:
            selected_recipe = json.loads(existing_user['selected_recipe'])

        skip_mode = existing_user['skip_mode']


    '''
    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_start_recipe'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'

                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_start_recipe'])

                    return jsonify(response)
                break
    '''


    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    # 첫번째 레시피 step 알림
    output['fulfillment_start_recipe'] = selected_recipe['recipe'][current_recipe_step] + ' 다 되시면, ' + \
                                         next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'

    update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    # 랜덤 음악 재생
    enable_music_play(response)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    # response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_start_recipe'])

    return jsonify(response)


@app.route('/answer.next', methods=['POST'])
def next():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

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

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        current_recipe_step = existing_user['recipe_step']

        if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
            output['fulfillment_next'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'

            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_next'])

            return jsonify(response)
        else:
            selected_recipe = json.loads(existing_user['selected_recipe'])

        skip_mode = existing_user['skip_mode']


    '''
    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    current_recipe_step = each_user_info['recipe_step']
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_next'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'

                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_next'])

                    return jsonify(response)

                break
    '''


    # 아직 마지막 단계가 아니라면 한 단계 증가
    if current_recipe_step != len(selected_recipe['recipe']) - 1:
        current_recipe_step += 1

    try:
        output['fulfillment_next'] = selected_recipe['recipe'][current_recipe_step]
    # list index out of range
    except IndexError:
        output['fulfillment_next'] = ''

    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    # 마지막 recipe step 이라면
    if current_recipe_step >= len(selected_recipe['recipe']) - 1:
        output['fulfillment_next'] += ' 이것이 요리의 마지막 안내입니다. 다시들으시려면 "아리아, 요리왕에서 처음부터 안내" 라고 말해주세요. 저는 안내를 종료하겠습니다. 다음에 또 이용해주세요.'
    else:
        output['fulfillment_next'] += ' 다 되시면, ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'
        # 랜덤 음악 재생
        enable_music_play(response)

    update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    # response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_next'])

    return jsonify(response)


@app.route('/answer.prev', methods=['POST'])
def prev():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

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

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        current_recipe_step = existing_user['recipe_step']

        if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
            output['fulfillment_prev'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'
            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_prev'])

            return jsonify(response)
        else:
            selected_recipe = json.loads(existing_user['selected_recipe'])

        skip_mode = existing_user['skip_mode']


    '''
    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    current_recipe_step = each_user_info['recipe_step']
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_prev'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_prev'])

                    return jsonify(response)
                break
    '''


    # 한 단계 감소
    current_recipe_step -= 1

    try:
        output['fulfillment_prev'] = selected_recipe['recipe'][current_recipe_step]
    # list index out of range
    except IndexError:
        output['fulfillment_prev'] = ''

    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    # 첫 번째 step 전으로 가려고 하면
    if current_recipe_step <= 0:
        output['fulfillment_prev'] += '이미 첫번째 단계입니다. ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'
        update_user_info_json_file(accessToken, action_name, 1, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)
    else:
        output['fulfillment_prev'] += ' 다 되시면, ' + next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'
        # 랜덤 음악 재생
        enable_music_play(response)
        update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    # response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_prev'])

    return jsonify(response)


@app.route('/answer.repeat', methods=['POST'])
def repeat():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

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

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        current_recipe_step = existing_user['recipe_step']

        if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
            output['fulfillment_repeat'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'
            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            # response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_repeat'])

            return jsonify(response)
        else:
            selected_recipe = json.loads(existing_user['selected_recipe'])

        skip_mode = existing_user['skip_mode']


    '''
    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    current_recipe_step = each_user_info['recipe_step']
                    selected_recipe = each_user_info['selected_recipe']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_repeat'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    # response['directives'] = None

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_repeat'])

                    return jsonify(response)
                break
    '''

    update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    # 다음 단계 예상 발화 랜덤 발생
    rand_num = random.randrange(0, len(next_step_invoke))

    try:
        output['fulfillment_repeat'] = selected_recipe['recipe'][current_recipe_step] + ' 다 되시면, ' + \
                                       next_step_invoke[rand_num] + ' 라고 이야기 해 주세요.'
        # 랜덤 음악 재생
        enable_music_play(response)
    except IndexError:
        output['fulfillment_repeat'] = '이것이 요리의 마지막 안내입니다. 다시 들으시려면 "아리아, 요리왕에서 처음부터 안내" 라고 말해주세요. 저는 안내를 종료하겠습니다. 다음에 또 이용해주세요.'

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    # response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_repeat'])

    return jsonify(response)


@app.route('/answer.start', methods=['POST'])
def start():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        current_recipe_step = existing_user['recipe_step']

        if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
            output['fulfillment_start'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_start'])

            return jsonify(response)
        else:
            selected_recipe = json.loads(existing_user['selected_recipe'])

        skip_mode = existing_user['skip_mode']


    '''
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

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_start'])

                    return jsonify(response)
                break
    '''


    # 레시피 설명하기 전 처음으로 가고자 할 경우
    if current_recipe_step == 0:
        output['fulfillment_start'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)
    # 레시피 설명 도중 처음으로 가고자 할 경우
    else:
        output['fulfillment_start'] = '다른 레시피를 추천해드릴까요? "응 해줘" 또는 "아니 괜찮아" 로 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_start'])

    return jsonify(response)


@app.route('/answer.confirm_yes', methods=['POST'])
def confirm_yes():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    need_oauth_reconnect = 0

    output['fulfillment_confirm_yes'] = ''

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        try:
            # confirm_yes intent로 들어오기 전에 무슨 action이었는지 확인하기 위한 용도
            before_action = existing_user['before_action']
            current_recipe_step = existing_user['recipe_step']

            if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
                selected_recipe = None
            else:
                selected_recipe = json.loads(existing_user['selected_recipe'])


            need_oauth_reconnect = existing_user['need_oauth_reconnect']
            run_count = existing_user['run_count']
            skip_mode = existing_user['skip_mode']
        except:
            output['fulfillment_confirm_yes'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_confirm_yes'])

            return jsonify(response)

    '''
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

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_confirm_yes'])

                    return jsonify(response)
                break
    '''

    if before_action == 'answer.start':
        output['fulfillment_confirm_yes'] = '한식, 중식, 일식, 양식, 분식 중에 선택해주시고, "한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)
    # 이메일 전송할 경우
    elif before_action == 'answer.ask_ingredients':
        # nugu builder 사용 혹은 계정 미연동
        if accessToken == 'dev':
            output['fulfillment_confirm_yes'] = 'NUGU builder로 테스트 하시거나, NUGU 앱에서 계정 연동을 하지 않으시면 이메일 발송이 불가능합니다.'
            output[
                'fulfillment_confirm_yes'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악 재생을 중지하고 싶으시면, "아리아, 종료" 혹은 "아리아, 그만" 이라고 말씀해주세요.'
            output['fulfillment_confirm_yes'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'

        # 계정 연동 해제 후 다시 연결해야 하는 경우
        elif need_oauth_reconnect == 1:
            output['fulfillment_confirm_yes'] = '이메일 발송을 원하시면 NUGU 앱에서 계정 연동을 해제하시고, 다시 연결해주세요.'
            output['fulfillment_confirm_yes'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악 재생을 중지하고 싶으시면, "아리아, 종료" 혹은 "아리아, 그만" 이라고 말씀해주세요.'
            output['fulfillment_confirm_yes'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'

        # nugu app에서 계정 연동
        else:
            t = threading.Thread(target=send_gmail_to_user, args=(
            accessToken, selected_recipe, action_name, current_recipe_step, run_count, skip_mode))
            t.start()

            output['fulfillment_confirm_yes'] = '레시피를 이메일로 발송하였습니다. 수신함을 확인해 보세요.'
            output[
                'fulfillment_confirm_yes'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악 재생을 중지하고 싶으시면, "아리아, 종료" 혹은 "아리아, 그만" 이라고 말씀해주세요.'
            output['fulfillment_confirm_yes'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'

        update_user_info_json_file(accessToken, action_name, 0, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    elif before_action == 'answer.ask_recipe':
        output[
            'fulfillment_confirm_yes'] = '고급 사용자 모드로 전환되었습니다. 한식, 중식, 일식, 양식, 분식 중에 선택해주시고, "한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, json.dumps(selected_recipe, ensure_ascii=False), 1)


    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_confirm_yes'])

    return jsonify(response)


@app.route('/answer.confirm_no', methods=['POST'])
def confirm_no():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'
    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        try:
            # confirm_no intent로 들어오기 전에 무슨 action이었는지 확인하기 위한 용도
            before_action = existing_user['before_action']

            if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
                selected_recipe = None
            else:
                selected_recipe = json.loads(existing_user['selected_recipe'])

            skip_mode = existing_user['skip_mode']
        except:
            output['fulfillment_confirm_no'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_confirm_no'])

            return jsonify(response)

    '''
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

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_confirm_no'])

                    return jsonify(response)
                break
    '''


    if before_action == 'answer.start':
        output['fulfillment_confirm_no'] = '그럼 현재 레시피를 처음 단계부터 다시 알려드릴게요.'
        output['fulfillment_confirm_no'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)
    # 이메일 전송 안하는 경우
    elif before_action == 'answer.ask_ingredients':
        output['fulfillment_confirm_no'] = '그럼 바로 레시피 안내를 시작할게요.'
        output[
            'fulfillment_confirm_no'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악 재생을 중지하고 싶으시면, "아리아, 종료" 혹은 "아리아, 그만" 이라고 말씀해주세요.'
        output['fulfillment_confirm_no'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)
    elif before_action == 'answer.ask_recipe':
        output[
            'fulfillment_confirm_no'] = '네, 그럼 원래대로 설명드리겠습니다. 한식, 중식, 일식, 양식, 분식 중에 선택해주시고, "한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
        update_user_info_json_file(accessToken, action_name, 0, json.dumps(selected_recipe, ensure_ascii=False), 0)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_confirm_no'])

    return jsonify(response)


@app.route('/answer.send_email', methods=['POST'])
def send_email():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    need_oauth_reconnect = 0

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        try:
            current_recipe_step = existing_user['recipe_step']

            if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
                selected_recipe = None
            else:
                selected_recipe = json.loads(existing_user['selected_recipe'])

            need_oauth_reconnect = existing_user['need_oauth_reconnect']
            run_count = existing_user['run_count']
            skip_mode = existing_user['skip_mode']
        except:
            output['fulfillment_send_email'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_send_email'])

            return jsonify(response)

    '''
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

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_send_email'])

                    return jsonify(response)
                break
    '''


    # nugu builder 사용 혹은 계정 미연동
    if accessToken == 'dev':
        output['fulfillment_send_email'] = 'NUGU builder를 사용하시거나, NUGU 앱에서 계정 연동을 하지 않으시면 이메일 발송이 불가능합니다.'
        output['fulfillment_send_email'] += ' 이메일로 레시피를 받아보시려면, NUGU 앱에서 계정 연동을 하시고 다시 시도해주세요.'
        # 레시피 설명 전
        if current_recipe_step == 0:
            output[
                'fulfillment_send_email'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악 재생을 중지하고 싶으시면, "아리아, 종료" 혹은 "아리아, 그만" 이라고 말씀해주세요.'
            output['fulfillment_send_email'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
        # 레시피 설명 중
        else:
            output['fulfillment_send_email'] += ' 레시피를 이어서 들으시려면 "다음안내 들려줘" 라고 말씀해주세요.'

    # 계정 연동 해제 후 다시 연결해야 하는 경우
    elif need_oauth_reconnect == 1:
        output['fulfillment_send_email'] = '이메일 발송을 원하시면 NUGU 앱에서 계정 연동을 해제하시고, 다시 연결해주세요.'
        output[
            'fulfillment_send_email'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악 재생을 중지하고 싶으시면, "아리아, 종료" 혹은 "아리아, 그만" 이라고 말씀해주세요.'
        output['fulfillment_send_email'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'

    # nugu app에서 계정 연동
    else:
        t = threading.Thread(target=send_gmail_to_user, args=(accessToken, selected_recipe, action_name, current_recipe_step, run_count, skip_mode))
        t.start()

        # 레시피 설명하기 전
        if current_recipe_step == 0:
            output['fulfillment_send_email'] = '레시피를 이메일로 발송하였습니다. 수신함을 확인해보세요.'
            output[
                'fulfillment_send_email'] += ' 요리하시는 동안 음악을 들려드릴건데요, 음악 재생을 중지하고 싶으시면, "아리아, 종료" 혹은 "아리아, 그만" 이라고 말씀해주세요.'
            output['fulfillment_send_email'] += ' 레시피 안내를 시작하시려면 "레시피 시작" 이라고 말씀해주세요.'
            update_user_info_json_file(accessToken, action_name, 0, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)
        # 레시피 설명중
        else:
            output['fulfillment_send_email'] = '레시피를 이메일로 발송하였습니다. 수신함을 확인해보세요. 레시피를 이어서 들으시려면 "다음안내 들려줘" 라고 말씀해주세요.'
            update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_send_email'])

    return jsonify(response)


@app.route('/answer.ask_music', methods=['POST'])
def ask_music():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        try:
            if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
                selected_recipe = None
            else:
                selected_recipe = json.loads(existing_user['selected_recipe'])

            current_recipe_step = existing_user['recipe_step']
            skip_mode = existing_user['skip_mode']
        except:
            output['fulfillment_ask_music'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'
            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_music'])

            return jsonify(response)

    '''
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
                    output['fulfillment_ask_music'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_music'])

                    return jsonify(response)
                break
    '''

    with open('./recently_played_music.json', 'r', encoding='utf-8') as f:
        music_info = json.load(f)
        music_title = music_info['music_title']

    output['fulfillment_ask_music'] = '방금 재생된 음악은 ' + music_title + ' 입니다.'
    output['fulfillment_ask_music'] += ' 다음 단계로 넘어가시려면 "아리아, 요리왕에서 다음 안내 들려줘" 라고 이야기 해 주세요.'

    update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_music'])

    return jsonify(response)


@app.route('/answer.ask_food_name', methods=['POST'])
def ask_food_name():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        try:
            if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
                selected_recipe = None
            else:
                selected_recipe = json.loads(existing_user['selected_recipe'])

            current_recipe_step = existing_user['recipe_step']
            skip_mode = existing_user['skip_mode']
        except:
            output['fulfillment_ask_food_name'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'
            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info(
                'triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_food_name'])

            return jsonify(response)

    '''
    with open('./user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        for each_user_info in user_info:
            if each_user_info['accessToken'] == accessToken:
                try:
                    selected_recipe = each_user_info['selected_recipe']
                    current_recipe_step = each_user_info['recipe_step']
                    skip_mode = each_user_info['skip_mode']
                except:
                    output['fulfillment_ask_food_name'] = '아리아, 요리왕에서 레시피 추천해줘 라고 먼저 말씀해주세요.'
                    response['version'] = '2.0'
                    response['resultCode'] = 'OK'
                    response['output'] = output
                    response['directives'] = None

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_food_name'])

                    return jsonify(response)
                break
    '''


    output['fulfillment_ask_food_name'] = '지금 만들고 계신 요리는 ' + selected_recipe['food_name'] + ' 입니다.'

    update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_ask_food_name'])

    return jsonify(response)


@app.route('/answer.help', methods=['POST'])
def help():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    mylogger = check_user(accessToken)

    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']


    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        try:
            if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
                selected_recipe = None
            else:
                selected_recipe = json.loads(existing_user['selected_recipe'])

            current_recipe_step = existing_user['recipe_step']
            # 전 action
            before_action = existing_user['before_action']
            # 전 전 action
            bef_bef_action = existing_user['bef_bef_action']
            skip_mode = existing_user['skip_mode']
        except:
            output['fulfillment_help'] = '레시피 추천해줘 라고 먼저 말씀해주세요.'
            response['version'] = '2.0'
            response['resultCode'] = 'OK'
            response['output'] = output
            response['directives'] = None

            # 로그 추가
            mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_help'])

            return jsonify(response)

    '''
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

                    # 로그 추가
                    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_help'])

                    return jsonify(response)
                break
    '''


    if before_action == 'answer.ask_recipe':
        output['fulfillment_help'] = '"한식 선택" 과 같이 "선택" 이란 단어를 붙여서 말씀해주세요.'
    elif before_action == 'answer.inform_food_type':
        output['fulfillment_help'] = '"재료 안내해줘" 라고 이야기 해 보세요.'
    elif before_action == 'answer.ask_ingredients' and bef_bef_action == 'answer.inform_food_type':
        output['fulfillment_help'] = '"응, 해줘" 또는 "아니야, 괜찮아" 라고 이야기 해 보세요.'
    elif before_action == 'answer.ask_ingredients' and (
            bef_bef_action == 'answer.start_recipe' or bef_bef_action == 'answer.next' or bef_bef_action == 'answer.repeat'):
        output[
            'fulfillment_help'] = '방금 단계를 다시 들으시려면 "아리아, 요리왕에서 방금 안내 한번더 들려줘" 라고 이야기 해 주시고, 다음 단계로 넘어가시려면 "아리아, 요리왕에서 다음 안내 들려줘" 라고 이야기 해 주세요.'
    elif before_action == 'answer.start_recipe' or before_action == 'answer.next' or before_action == 'answer.repeat' or before_action == 'answer.prev':
        output[
            'fulfillment_help'] = '"아리아, 요리왕에서 다음안내 들려줘" 라고 이야기 해보세요. 재료설명을 듣고 싶으시면 "아리아, 요리왕에서 재료 안내해줘" 라고 이야기 해보세요.'
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

    update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_help'])

    return jsonify(response)


@app.route('/answer.tutorial', methods=['POST'])
def tutorial():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    response = {}
    req = json.loads(request.data.decode('utf-8'))
    print(json.dumps(req, indent=4))

    try:
        accessToken = req['context']['session']['accessToken']
    except:
        accessToken = 'dev'

    action_name = req['action']['actionName']
    parameters = req['action']['parameters']

    mylogger = check_user(accessToken)

    existing_user = db_helper.select_by_token(accessToken)
    if existing_user != None:
        try:
            if existing_user['selected_recipe'] == None or existing_user['selected_recipe'] == 'None':
                selected_recipe = None
            else:
                selected_recipe = json.loads(existing_user['selected_recipe'])

            current_recipe_step = existing_user['recipe_step']
            skip_mode = existing_user['skip_mode']
        except:
            selected_recipe = None
            current_recipe_step = 0
            skip_mode = 0

    '''
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
                    skip_mode = 0
                break
    '''


    output = {}
    for param in parameters:
        output[param] = parameters[param]['value']

    output['fulfillment_tutorial'] = '요리왕에서 할 수 있는 것을 알려드립니다. 처음부터 들으시려면 "처음부터 안내해줘"라고, 재료안내를 원하시면 "재료 안내해줘" 라고 말해보세요.'
    output['fulfillment_tutorial'] += ' 그 외, 부가기능도 있습니다.'
    output['fulfillment_tutorial'] += ' 이메일로 레시피를 받으시려면 "이메일로 레시피 보내줘", 노래 제목이 궁금하시면 "방금 재생된 음악 알려줘" 라고 말해보세요.'
    output['fulfillment_tutorial'] += ' 사용법을 다시들으시려면 "사용법 알려줘"라고, 시작하시려면 "레시피 추천해줘" 라고 말씀하세요.'

    update_user_info_json_file(accessToken, action_name, current_recipe_step, json.dumps(selected_recipe, ensure_ascii=False), skip_mode)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output
    response['directives'] = None

    # 로그 추가
    mylogger.info('triggered action : ' + action_name + ' | fulfillment : ' + output['fulfillment_tutorial'])

    return jsonify(response)



@app.route('/answer.music_finished', methods=['POST'])
def music_finished():

    response = {}
    output = {}

    enable_music_play(response)

    response['version'] = '2.0'
    response['resultCode'] = 'OK'
    response['output'] = output

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
    app.run(host='0.0.0.0', port=config.PORT, debug=True, threaded=True)