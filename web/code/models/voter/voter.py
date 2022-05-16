from flask import Blueprint, render_template, request, jsonify, send_from_directory, send_file
import os
from subprocess import Popen
from subprocess import PIPE, STDOUT
from pathlib import Path
import datetime

voter = Blueprint('voter', __name__, template_folder='templates')

def bash(command, cwd, output=True, logfile=None):
#     if output:print(command)
    p = Popen(command, cwd=cwd, stdout=PIPE, stderr=STDOUT, shell=True)
#     p.wait()
    if output:
        if logfile == None:
            while True:
                logs = p.stdout.readline()
                logs = bytes.decode(logs)
                print(logs.strip())
                if logs == '' and p.poll() is not None:
                    break
        else:
            with open(logfile, 'a') as fw:
                while True:
                    logs = p.stdout.readline()
                    logs = bytes.decode(logs)
                    print(logs.strip())
                    fw.write(logs)
                    if logs == '' and p.poll() is not None:
                        break
    else:
        p.wait()

folder = Path('/Kingcolon/server/public/upload/newaudio')
format_audio_folder = Path('/home/ubuntu/kingcolon_audio/format_audio')

@voter.route('/', methods=['GET', 'POST'])
def index():
    date_list = []
    for date_folder in format_audio_folder.glob('*'):
        audio_count = len(list(date_folder.glob('*.wav')))
        date = date_folder.name
        final_dict = start_vote_date(date)
        total = len(final_dict)
        error = 0
        for k,v in final_dict.items():
            if v[0] != v[1]:
                if v[0] != '':
                    error += 1
        error_rate = round(error / total * 100, 3) 
        date_list.append([date_folder.stem, audio_count, error_rate])
    date_list.sort()
    return render_template('voter_index.html', date_list=date_list)

@voter.route('/<date>', methods=['GET', 'POST'])
def date_index(date):
    date_folder = format_audio_folder / date
    final_dict = {}
    with open(date_folder / 'text') as f1, open(date_folder / 'vote_hyp.txt') as f2:
        for l1, l2 in zip(f1, f2):
            try:
                n1, hyp = l1.strip().split(' ', 1)
            except:
                n1 = l1.strip()
                hyp = ''
            try:
                n2, ref = l2.strip().split(' ', 1)
            except:
                n2 = l2.strip()
                ref = ''
            assert n1 == n2
            assert n1 not in final_dict
            final_dict[n1] = [ref, hyp]
    wav_list = []
    for wav_file in date_folder.glob('*.wav'):
        name = wav_file.stem
        time = datetime.datetime.fromtimestamp(wav_file.stat().st_ctime)
        wav_list.append([name, time, final_dict[name][0], final_dict[name][1]])
        # wav_list.append([name, time, str(wav_file)])
    wav_list.sort()
    return render_template('voter_date.html', date=date, wav_list=wav_list, date_folder=str(date_folder))

@voter.route('/<date>/<wavfile>', methods=['GET', 'POST'])
def date_index_wav(date, wavfile):
    date_folder = format_audio_folder / date
    wav_file = date_folder / (Path(wavfile).name + '.wav')
    return send_file(str(wav_file), as_attachment=False)

@voter.route('/date_type', methods=['POST'])
def do_click():

    command = 'python3 format_audio.py'
    bash(command=command, cwd='/web/code/models/voter')
        

    import random
    aa = random.randint(1, 20)

    return jsonify(ttt=aa)

def do_recog(model_name, test_folder):
    model_folder = Path('/web/code/models/voter/paks-test-vote/')
    num_jobs = 4
    model = '{}.pak'.format(model_name)
    wavscp = test_folder / "wav.scp"
    outlog = test_folder / "{}_log.txt".format(model_name)
    logfile = test_folder / 'vote_logs.txt'
    command = './cpu_decoder -c {} -j {} -s {} -b 1 -o {}'.format(str(model), str(num_jobs), str(wavscp), str(outlog))
    cwd = str(model_folder)
    bash(command=command, cwd=cwd, logfile=logfile)

def start_vote_date(date):
    voter_dict = {}
    test_folder = Path('/home/ubuntu/kingcolon_audio/format_audio/{}'.format(date))
    assert (test_folder / 'text').exists()
    with open(test_folder / 'text') as fp:
        for line in fp:
            name_id, text = line.strip().split(' ', 1)
            assert name_id not in voter_dict
            voter_dict[name_id] = {'ref':text, 'hyp':[]}

    overwrite_voter_hyp = True  
    models = ['alim', 'kenkone_evas_v3.1', 'kenkone_evas_v4.5', 'kenkone_evas_v4.6', 'evas_small_catnoise_v1']
    models_weight = [1, 1, 2, 2, 3]
    logfile = test_folder / 'vote_logs.txt'
    for model_name in models:
        outlog = test_folder / "{}_log.txt".format(model_name)
        
        if outlog.exists() == False:
            do_recog(model_name, test_folder)
            overwrite_voter_hyp = True
            
        test_dict = {}
        with open(outlog) as fp:
            for line in fp:
                try:
                    name_id, text = line.strip().split(' ', 1)
                except:
                    name_id = line.strip()
                    text = ''
                assert name_id not in test_dict
                test_dict[name_id] = text
        for k,v in voter_dict.items():
            if k not in test_dict:
                do_recog(model_name, test_folder)
                overwrite_voter_hyp = True
                break


    ## 有些音檔壞掉導致cpu_decoder不會辨識  把這些音檔當空字串寫回log裡 <--
    for model_name in models:
        outlog = test_folder / "{}_log.txt".format(model_name)

        test_dict = {}
        with open(outlog) as fp:
            for line in fp:
                try:
                    name_id, text = line.strip().split(' ', 1)
                except:
                    name_id = line.strip()
                    text = ''
                assert name_id not in test_dict
                test_dict[name_id] = text
        for k,v in voter_dict.items():
            if k not in test_dict:
                with open(outlog, 'a') as fw:
                    fw.write(k + ' ' + '' + '\n')

    ## 有些音檔壞掉導致cpu_decoder不會辨識  把這些音檔當空字串寫回log裡 -->

    for model_name, model_weight in zip(models, models_weight):
        outlog = test_folder / "{}_log.txt".format(model_name)
        with open(outlog) as fp:
            for line in fp:
                try:
                    name_id, text = line.strip().split(' ', 1)
                except:
                    name_id = line.strip()
                    text = ''
                assert name_id in voter_dict
                for i in range(model_weight):
                    voter_dict[name_id]['hyp'].append(text)

    vote_hyp = test_folder / 'vote_hyp.txt'
    if vote_hyp.exists() == False or overwrite_voter_hyp:
        with open(vote_hyp, 'w') as fw: 
            for k, v in voter_dict.items():
                hyps = v['hyp']
                ans = max(hyps, key = hyps.count)
                fw.write(k + ' ' + ans + '\n')

    final_dict = {}
    with open(test_folder / 'text') as f1, open(vote_hyp) as f2:
        for l1, l2 in zip(f1, f2):
            try:
                n1, hyp = l1.strip().split(' ', 1)
            except:
                n1 = l1.strip()
                hyp = ''
            try:
                n2, ref = l2.strip().split(' ', 1)
            except:
                n2 = l2.strip()
                ref = ''
            assert n1 == n2
            assert n1 not in final_dict
            final_dict[n1] = [ref, hyp]

    return final_dict


        