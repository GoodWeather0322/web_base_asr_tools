from unicodedata import name
from flask import Blueprint, render_template, request, jsonify, send_from_directory
import re
from pathlib import Path
from flask import current_app
import base64
import json
from datetime import datetime, timedelta

corrector = Blueprint('corrector', __name__, template_folder='templates')

@corrector.route('/', methods=['GET', 'POST'])
def index():
    audio_folder = Path("/home/ubuntu/evas_audio/")
    site_list = []
    for site_folder in sorted(audio_folder.glob('*')):
        if site_folder.is_dir() == False:
            continue
        site_list.append(site_folder.name)

    return render_template('corrector_index.html', site_list=site_list)

@corrector.route('/<site>', methods=['GET', 'POST'])
def site_index(site):
    audio_folder = Path("/home/ubuntu/evas_audio/")
    site_folder = audio_folder / site
    regex = '\d{4}-\d{2}-\d{2}'
    date_list = []
    for date_folder in sorted(site_folder.glob('*')):
        if date_folder.is_dir() == False:
            continue
        date = date_folder.name
        if re.fullmatch(regex, date) == None:
            continue
        date_list.append(date)

    return render_template('corrector_site.html', site=site, date_list=date_list)

@corrector.route('/<site>/<date>', methods=['GET', 'POST'])
def date_index(site, date):
    audio_folder = Path("/home/ubuntu/evas_audio/")
    site_folder = audio_folder / site
    date_folder = site_folder / date
    datas = []
    current_app.logger.info('LOAD DATE FOLDER : {}'.format(date))
    if (date_folder / 'text.new').exists():
        with open(date_folder / 'text') as f1, open(date_folder / 'wav.scp') as f2, open(date_folder / 'text.new') as f3:
            for l1, l2, l3 in zip(f1, f2, f3):
                try:
                    n1, t = l1.strip().split(' ', 1)
                except:
                    n1 = l1.strip()
                    t = ''

                try:
                    n3, correct = l3.strip().split(' ', 1)
                except:
                    n3 = l3.strip()
                    correct = ''

                n2, w = l2.strip().split(' ', 1)
                w = Path(w).name
                w = date_folder / w
                w = str(w)

                assert n1 == n2 == n3
                datas.append([n1, t, correct, w])
    else:
        with open(date_folder / 'text') as f1, open(date_folder / 'wav.scp') as f2:
            for l1, l2 in zip(f1, f2):
                try:
                    n1, t = l1.strip().split(' ', 1)
                except:
                    n1 = l1.strip()
                    t = ''
                n2, w = l2.strip().split(' ', 1)
                w = Path(w).name
                w = date_folder / w
                w = str(w)

                assert n1 == n2
                datas.append([n1, t, '', w])
        # current_app.logger.info(datas)   

    time_log = []
    total_time = None
    if (date_folder / 'work_time_log.txt').exists():
        with open(date_folder / 'work_time_log.txt') as fp:
            lines = fp.readlines()
            for i, line in enumerate(lines):
                if lines[i][:5] == '-----':
                    continue
                elif lines[i][:5] == 'start':
                    if i == len(lines) - 1:
                        continue
                    if lines[i+1][:5] == 'end  ':
                        start = lines[i][5:].strip()
                        end = lines[i+1][5:].strip()
                        time_log.append([start, end])
                        if total_time == None:
                            total_time = datetime.strptime(end, '%Y-%m-%d %H:%M:%S') - datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                        else:
                            total_time += datetime.strptime(end, '%Y-%m-%d %H:%M:%S') - datetime.strptime(start, '%Y-%m-%d %H:%M:%S')

                        current_app.logger.info('total_time : ' + str(total_time))
    else:
        pass

    return render_template('corrector_date.html', site=site, date=date, datas=datas, time_log=time_log, total_time=str(total_time))

@corrector.route('/getbyte', methods=['POST'])
def get_byte():
    wav_file = request.form['wav_file']
    
    # current_app.logger.info(Path(wav_file).parent.exists())
    with open(wav_file, 'rb') as f:
        wav_byte = f.read()

    audio_data = base64.b64encode(wav_byte).decode('UTF-8')
    # current_app.logger.info(audio_data)
    return jsonify(audio_data=audio_data)

@corrector.route('/savetext', methods=['POST'])
def save_text():

    site = request.form['site']
    date = request.form['date']
    array = request.form['array']
    array = eval(array)
    current_app.logger.info(date)
    current_app.logger.info(array)

    audio_folder = Path("/home/ubuntu/evas_audio/")
    site_folder = audio_folder / site
    date_folder = site_folder / date
    
    with open(date_folder / 'text.new', 'w') as fw:
        for name_id, text in array:
            fw.write(name_id.strip() + ' ' + text.strip() + '\n')
    
    return jsonify(flag='success')

@corrector.route('/savetimerecord', methods=['POST'])
def save_time_record():

    site = request.form['site']
    date = request.form['date']
    flag = request.form['flag']
    time = request.form['time']

    date_time = datetime.fromtimestamp(int(time)/1000.0)
    date_time = date_time + timedelta(hours=8)

    current_app.logger.info(date)
    current_app.logger.info(flag)
    current_app.logger.info(date_time)

    audio_folder = Path("/home/ubuntu/evas_audio/")
    site_folder = audio_folder / site
    date_folder = site_folder / date

    if (date_folder / 'work_time_log.txt').exists():
        with open(date_folder / 'work_time_log.txt') as fp:
            line = fp.readlines()[-1]
        if flag == 'end' and line[:5] != 'start':
            current_app.logger.info('time log error, fix it')
            return jsonify(flag='log error')

        elif flag == 'start' and line[:5] != '-----':
            current_app.logger.info('time log error, fix it')
            line = line.replace('start', 'end  ')
            with open(date_folder / 'work_time_log.txt', 'a') as fw:
                fw.write(line)
                fw.write('-'*20 + '\n')

    with open(date_folder / 'work_time_log.txt', 'a') as fw:
        if flag == 'end':
            fw.write(flag + '   ' + date_time.strftime('%Y-%m-%d %H:%M:%S') + '\n')
            fw.write('-'*20 + '\n')
        else:
            fw.write(flag + ' ' + date_time.strftime('%Y-%m-%d %H:%M:%S') + '\n')

    
    return jsonify(flag='success')