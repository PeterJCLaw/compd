
import os.path
import subprocess
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def setup_module():
    """ Start redis """
    subprocess.call([os.path.join(ROOT, 'start-redis')])

def teardown_module():
    """ Stop redis """
    subprocess.call([os.path.join(ROOT, 'stop-redis')])

def check_output(*args):
    commander = os.path.join(ROOT, 'command')
    args_list = list(args)
    args_list.insert(0, commander)
    output = subprocess.check_output(args_list)
    assert output is not None
    print output
    return output

def test_version():
    version = check_output('version')
    assert len(version) > 4
    assert len(version) <= 40

def test_teams():
    teams_info_yaml = check_output('list-teams', '--yaml')
    teams_info = yaml.load(teams_info_yaml)
    assert 'list' in teams_info
    # Can't assert about the data