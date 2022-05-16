from flask import Blueprint, render_template, request, jsonify
from jinja2 import Markup
from pyecharts import options as opts
from pyecharts.charts import Bar
import datetime
from pathlib import Path
import sys
import soundfile as sf

commands = Blueprint('commands', __name__, template_folder='templates')
folder = Path('/Kingcolon/server/public/upload/newaudio')

@commands.route('/', methods=['GET', 'POST'])
def index():
    wavs = {}
    need_overwrite = False
    if Path('/web/code/models/commands/rec2dur').exists():
        with open('/web/code/models/commands/rec2dur') as fp:
            for line in fp:
                n, t = line.strip().split()
                wavs[n] = float(t)
        for sub_folder in folder.glob('*'):
            if sub_folder.is_dir() == False:
                continue
            # print(sub_folder, file=sys.stderr)
            for wav_file in sub_folder.glob('*.wav'):
                if wav_file.stem in wavs:
                    continue
                need_overwrite = True
                data, sr = sf.read(str(wav_file))
                wavs[wav_file.stem] = round(len(data) / sr, 4)

        if need_overwrite:
            with open('/web/code/models/commands/rec2dur', 'w') as fw:
                for k,v in wavs.items():
                    fw.write(k + ' ' + str(v) + '\n')
    else:
        need_overwrite = True
        with open('/web/code/models/commands/rec2dur', 'w') as fw:
            for sub_folder in folder.glob('*'):
                if sub_folder.is_dir() == False:
                    continue
                # print(sub_folder, file=sys.stderr)
                for wav_file in sub_folder.glob('*.wav'):
                    data, sr = sf.read(str(wav_file))
                    wavs[wav_file.stem] = round(len(data) / sr, 4)
                    fw.write(wav_file.stem + ' ' + str(wavs[wav_file.stem]) + '\n')
     
    total_time = 0
    total_file = 0
    for k,v in wavs.items():
        total_time += v
        total_file += 1
    total_time = str(round(total_time / 3600, 2))
    return render_template('commands_index.html', total_time=total_time, total_file=total_file)

@commands.route('/date_type', methods=['POST'])
def date_type():
    query = request.form['query']
    count = 0
    data = {}
    
    for sub_folder in folder.glob('*'):
        if sub_folder.is_dir() == False:
            continue
        # print(sub_folder, file=sys.stderr)
        for wav_file in sub_folder.glob('*.wav'):
            ctime = datetime.datetime.fromtimestamp(wav_file.stat().st_mtime)
            # print(wav_file, file=sys.stderr)
            if query == '1':
                if ctime.date() not in data:
                    data[ctime.date()] = 1
                else:
                    data[ctime.date()] += 1

            if query == '2':
                week = ctime.isocalendar()[1]
                if week not in data:
                    data[week] = 1
                else:
                    data[week] += 1

            if query == '3':
                month = ctime.date().month
                if month not in data:
                    data[month] = 1
                else:
                    data[month] += 1



    date = list(data.keys())
    date.sort()
    value = []
    for d in date:
        value.append(data[d])
    

    c = bar_base(date, value)

    return jsonify(test=query, myechart=Markup(c.render_embed()))


def bar_base(date, value) -> Bar:
    c = (
        Bar(init_opts=opts.InitOpts(width="1200px", height="600px"))
            .add_xaxis(date)
            .add_yaxis("value", value)
            .set_global_opts(title_opts=opts.TitleOpts(title="Bar-指令統計", subtitle=""))
    )

    return c