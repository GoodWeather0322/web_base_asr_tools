from pathlib import Path
from datetime import datetime
import shutil

audio_path = Path("/Kingcolon/server/public/upload/newaudio/")
new_audio_path = Path("/home/ubuntu/kingcolon_audio/format_audio")

new_audio_path.mkdir(exist_ok=True, parents=True)

dateFormatter = "%Y %b %d %H:%M:%S"

for person_file in audio_path.glob('*'):
    for text_file in person_file.glob('*.txt'):
        print(text_file)
        
        with open(text_file) as fp:
            for line in fp:
                if 'Coordinated Universal Time' in line:
                    try:
                        hyp, file_name, utc = line.strip().split('-')
                    except:
                        print(line.strip())
                    
                    if (audio_path / person_file / file_name).exists() == False:
                        continue
                    
                    seven, month, day, year, time, _ = utc.split(' ', 5)
                    dateString = ' '.join([year, month, day, time])
                    date = datetime.strptime(dateString, dateFormatter)
                    folder_name = date.strftime("%Y-%m-%d")
                    
                    if (new_audio_path / folder_name).exists() == False:
                        (new_audio_path / folder_name).mkdir(exist_ok=True, parents=True)
                    
                    if (new_audio_path / folder_name / file_name).exists() == False:
                        shutil.copy(audio_path / person_file / file_name, new_audio_path / folder_name / file_name)
                        
                        with open(new_audio_path / folder_name / 'wav.scp', 'a') as f1, \
                        open(new_audio_path / folder_name / 'text', 'a') as f2:
                            f1.write(Path(file_name).stem + ' ' + str(new_audio_path / folder_name / file_name))
                            f1.write('\n')
                            f2.write(Path(file_name).stem + ' ' + hyp)
                            f2.write('\n')