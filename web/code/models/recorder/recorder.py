from genericpath import exists
from multiprocessing import parent_process
import site
from flask import Blueprint, render_template, request, jsonify
from flask import flash, current_app
from pathlib import Path
import json
import wave
import base64
import random


recorder = Blueprint('recorder', __name__, template_folder='templates', static_folder='static')
record_folder = Path('/home/ubuntu/recorder_audio_folder/')

@recorder.route('/', methods=['GET', 'POST'])
def index():

    current_app.logger.info('='*20)
    current_app.logger.info('RECORDER INDEX')
    current_app.logger.info('='*20)

    site_list = []
    for site_folder in sorted(record_folder.glob('*')):
        current_app.logger.info("123  {}".format(site_folder))
        if site_folder.is_dir() == False:
            continue
        if site_folder.name == 'command_pack':
            continue
        site_list.append(site_folder.name)
    

    return render_template('recorder_index.html', site_list=site_list)

@recorder.route('/<site>', methods=['GET', 'POST'])
def login(site):
    command_files = list(Path('/home/ubuntu/recorder_audio_folder/command_pack/').glob("command_*.txt"))
    return render_template('recorder_login.html', site=site, command_files_count=len(command_files))

@recorder.route('/commandlist-handler', methods=['POST'])
def get_command_list():
    try:
        data = request.get_json()
        commandlist_id = data['command_list_id']
        current_app.logger.info('load command list : ' + commandlist_id)

        commands = []
        with open(record_folder / 'command_pack' / 'command_v2_{}.txt'.format(commandlist_id)) as fp:
            for line in fp:
                idx, command, real_command, wav_name = line.strip().split('\t')
                commands.append([idx, command, wav_name])

        return jsonify(flag='success', commands=commands)
    except Exception as e:
        current_app.logger.info(str(e))
        return jsonify(flag='false')

@recorder.route('/user-handler', methods=['POST'])
def check_userinfo():
    try:
        data = request.get_json()

        username = data['username']
        email = data['email']
        site = data['site']
        current_app.logger.info(username)
        current_app.logger.info(email)
        current_app.logger.info(site)
        current_app.logger.info('='*20)
        current_app.logger.info('='*20)

        site_record_folder = record_folder / site
        site_record_folder.mkdir(exist_ok=True, parents=True)

        ## record user info to json file
        if (site_record_folder / 'user_info.json').exists() == False:
            empty = {}
            empty['email'] = {}
            with open(site_record_folder / 'user_info.json', 'w') as fp:
                json.dump(empty, fp)

        with open(site_record_folder / 'user_info.json', 'r') as fp:
            user_info = json.load(fp)

        current_app.logger.info(user_info)
        current_app.logger.info('='*20)
        current_app.logger.info('='*20)
        if email not in user_info['email']:
            user_info['email'][email] = {'name':username}

        with open(site_record_folder / 'user_info.json', 'w') as fp:
            json.dump(user_info, fp, indent=4)
        
        ## create user folder , is exist: restore
        user_record_folder = site_record_folder / email
        user_record_folder.mkdir(exist_ok=True, parents=True)

        ## return user info and already command
        return jsonify(flag='success')
    except Exception as e:
        current_app.logger.info(str(e))
        return jsonify(flag='false')

@recorder.route('/commandsave-handler', methods=['POST'])
def check_save_command():

    try:
        data = request.get_json()

        username = data['username']
        email = data['email']
        site = data['site']
        commandlist_id = data['command_list_id']

        commands_dict = {}
        with open(record_folder / 'command_pack' / 'command_v2_{}.txt'.format(commandlist_id)) as fp:
            for line in fp:
                idx, command, real_command, wav_name = line.strip().split('\t')
                commands_dict[idx] = {'text':command, 'save':False}

        site_record_folder = record_folder / site
        user_record_folder = site_record_folder / email

        current_app.logger.info("CHECK USER : " + str(site_record_folder))
        current_app.logger.info("CHECK USER : " + str(user_record_folder))

        for k, v in commands_dict.items():
            wav_file = user_record_folder / '{}.wav'.format(k)
            # current_app.logger.info("check command ID {} saved or not".format(k))
            if wav_file.exists():
                commands_dict[k]['save'] = True
                # current_app.logger.info("SAVED")
            else:
                # current_app.logger.info("NOT")
                pass

        # current_app.logger.info(commands_dict)
        commands = []
        for k, v in commands_dict.items():
            commands.append([k, v['text'], v['save']])
        # current_app.logger.info(commands)

        return jsonify(flag='success', commands=commands)

    except Exception as e:
        current_app.logger.info(str(e))
        return jsonify(flag='false')

@recorder.route('/getsample', methods=['POST'])
def get_sample():
    voice_list = ['en-US-Wavenet-A', 'en-US-Wavenet-B', 'en-US-Wavenet-C', 'en-US-Wavenet-D',
             'en-US-Wavenet-E', 'en-US-Wavenet-F', 'en-US-Wavenet-G', 'en-US-Wavenet-H',
             'en-US-Wavenet-I', 'en-US-Wavenet-J']
    voice = random.choice(voice_list)
    wav_name = request.form['wav_name']
    command_audio_folder = record_folder / 'command_pack' / 'command_audio'
    wav_file = command_audio_folder / voice / '{}_{}.wav'.format(voice, wav_name)

    with open(wav_file, 'rb') as f:
        wav_byte = f.read()
    audio_data = base64.b64encode(wav_byte).decode('UTF-8')

    return jsonify(flag='success', wav_name=wav_name, audio_data=audio_data)

@recorder.route('/getplayback', methods=['POST'])
def get_playback():
    sampleId = request.form['sampleId']
    site = request.form['site']
    email = request.form['email']
    current_app.logger.info(sampleId)
    current_app.logger.info(site)
    current_app.logger.info(email)

    wav_file = record_folder / site / email / "{}.wav".format(sampleId)

    with open(wav_file, 'rb') as f:
        wav_byte = f.read()
    audio_data = base64.b64encode(wav_byte).decode('UTF-8')

    return jsonify(flag='success', email=email, sampleId=sampleId, audio_data=audio_data)

@recorder.route('/save-record', methods=['POST'])
def save_record():
    
    username = request.form['username']
    email = request.form['email']
    site = request.form['site']
    commandlist_id = request.form['commandlist_id']
    nowid = request.form['nowid']
    blob = request.files['audio']
    # blob = request.files['audio']
    current_app.logger.info(username)
    current_app.logger.info(email)
    current_app.logger.info(site)
    current_app.logger.info(nowid)
    # current_app.logger.info(len(blob))
    current_app.logger.info(request.files['audio'].mimetype)

    user_record_folder = record_folder / site / email
    file_name = str(user_record_folder / '{}.wav'.format(nowid))

    blob.save(file_name)
    
    commands_dict = {}
    with open(record_folder / 'command_pack' / 'command_v2_{}.txt'.format(commandlist_id)) as fp:
        for line in fp:
            idx, command, real_command, wav_name= line.strip().split('\t')
            commands_dict[idx] = {'text':command, 'save':False}

    for wav_file in user_record_folder.glob('*.wav'):
        idx = wav_file.stem
        # current_app.logger.info(idx)
        if idx in commands_dict:
            # current_app.logger.info(idx)
            # current_app.logger.info('='*20)
            # current_app.logger.info('='*20)
            commands_dict[idx]['save'] = True

    # current_app.logger.info(commands_dict)
    commands = []
    for k, v in commands_dict.items():
        commands.append([k, v['text'], v['save']])
    # current_app.logger.info(commands)

    ## return user info and already command
    return jsonify(flag='success', commands=commands, )
