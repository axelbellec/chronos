import click
from flask_script import Manager, Shell

from app import app
from app import NAMESPACE

def make_shell_context():
    return dict(app=app)

manager = Manager(app)
manager.add_command('shell', Shell(make_context=make_shell_context))

@manager.command
def runserver():
    """ Run webserver. """

    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=True, use_reloader=True)

if __name__ == '__main__':
    manager.run()