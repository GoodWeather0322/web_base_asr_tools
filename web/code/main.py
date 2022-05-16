from flask import Flask, Blueprint, render_template
from flask_bootstrap import Bootstrap
from models.commands.commands import commands
from models.voter.voter import voter
from models.corrector.corrector import corrector
from models.recorder.recorder import recorder

app = Flask(__name__, 
    template_folder='templates', 
    static_folder='templates/static',
    static_url_path='/static')

Bootstrap(app)

app.register_blueprint(commands, url_prefix='/commands')
app.register_blueprint(voter, url_prefix='/voter')
app.register_blueprint(corrector, url_prefix='/corrector')
app.register_blueprint(recorder, url_prefix='/recorder')


@app.route('/', methods=['GET'])
def app_index():
    return render_template('home_index.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)