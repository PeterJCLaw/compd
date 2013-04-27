
from collections import defaultdict
from datetime import date, datetime, timedelta

import talk

# Set the delay of the current
DELAYS = {
    date(2013, 04, 13): timedelta(minutes = 6),
    date(2013, 04, 14): timedelta(minutes = 0)
}

# Over-estimate for optimisation
TOTAL_MATCHES = 150

MATCH_ID = 'match-{0}'

_team_cache = {}

def get_team_name(tla):
    if tla not in _team_cache:
        team_data = talk.command_yaml('team {0}'.format(tla))
        #print tla, team_data
        name = team_data['team']['name']
        _team_cache[tla] = name

    return _team_cache[tla]

def format_name(tla, name):
    if name is not None:
        name = '{0}: {1}'.format(tla, name)
    else:
        name = tla
    return name

def get_delayed_time(original):
    orig_date = original.date()
    delay = DELAYS.get(orig_date, timedelta(0))
    new_dt = original + delay
    return new_dt

_team_list = None
def get_team_list():
    global _team_list
    if _team_list is None:
        team_data = talk.command_yaml('list-teams')
        _team_list = team_data['list']

    return _team_list

def gen_pts_tla(points_sorted, points_map):
    for pts in points_sorted:
        for tla in points_map[pts]:
            yield pts, tla

def get_sorted_league_points():
    team_list = get_team_list()

    pts_map = defaultdict(lambda: [])

    for tla in team_list.keys():
        league_data = talk.command_yaml('get-league-points {0}'.format(tla))
        pts = league_data['points']
        pts = pts if pts else 0
        pts_map[pts].append(tla)

    pts_list = sorted(pts_map.keys(), reverse=True)
    pos = 1

    sorted_tuples = gen_pts_tla(pts_list, pts_map)
    return sorted_tuples

def get_all_league_rows(row_limit = None):
    tuples = get_sorted_league_points()
    row = 1
    last_pts = 0
    for pts, tla in tuples:
        pos = row
        if last_pts == pts:
            pos = ''
        else:
            last_pts = pts
        yield pts, tla, pos
        if row_limit is not None and row >= row_limit:
            break
        row += 1

_all_match_scores = None
def get_all_match_scores():
    global _all_match_scores
    if _all_match_scores is None:
        _all_match_scores = {}
        for n in range(1, TOTAL_MATCHES + 1):
            ident = MATCH_ID.format(n)
            scores = talk.command_yaml('get-scores {0}'.format(ident))
            _all_match_scores[ident] = scores['scores']
    return _all_match_scores

def last_scored_match():
    all_scores = get_all_match_scores()
    for n in range(1, TOTAL_MATCHES + 1):
        ident = MATCH_ID.format(n)
        scores = all_scores[ident]
        if scores is None:
            return int(ident[6:]) - 1
    return n

class HTMLSchedule(object):
    def __init__(self, schedule):
        self._schedule = schedule

    def get_header(self, date):
        out = '\n<h2>{0}</h2>'.format(date.strftime('%A, %d %B %Y'))
        out += '\n<table class="match-schedule"><thead><tr>'
        out += '\n<th> Time </th><th> Match </th><th> Zone 0 </th><th> Zone 1 </th><th> Zone 2 </th><th> Zone 3 </th>'
        out += '\n</tr></thead><tbody>'
        return out

    def get_tail(self):
        return '</tbody></table>'

    def get_team_cell(self, team_id, show_name = False):
        name = get_team_name(team_id)
        if show_name:
            id_html = '<span class="team-id">{0}</span>'.format(team_id)
            name_html = '<span class="team-name">{0}</span>'.format(name)
            text = format_name(id_html, name_html)
        else:
            text = '<span class="team-id" title="{1}">{0}</span>'.format(team_id, name)

        return '<td class="team-{0}">{1}</td>'.format(team_id, text)

    def get_row(self, time, num, teams, show_team_name = False):
        out = '\n<tr class="match-{0}">'.format(int(num))
        cells = [self.get_team_cell(tid, show_team_name) for tid in teams]
        out += "\n\t<td>{0}</td><td>{1}</td>{2}".format(time, num, ''.join(cells))
        out += "\n</tr>"
        return out

    def get_all(self):
        date = None
        output = '<h1>Match Schedule</h1>'

        for ident, stamp in self._schedule:
            dt = datetime.fromtimestamp(stamp)
            dt = get_delayed_time(dt)
            teams_data = talk.command_yaml('get-match-teams {0}'.format(ident))
            #print teams_data
            team_ids = teams_data['teams']
            this_date = dt.date()
            if date != this_date:
                if date is not None:
                    output += self.get_tail()
                date = this_date
                output += self.get_header(date)
            num = ident[6:]
            output += self.get_row(dt.time(), num, team_ids, True)

        output += self.get_tail()
        return output
