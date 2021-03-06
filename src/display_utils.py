
from collections import defaultdict
from datetime import date, datetime, timedelta

from poltergeist.config import config
import talk

MAX_POS = config.get('display', 'leaderboard_size')
TOTAL_MATCHES = config.get('display', 'total_matches')

QUALIFYING_TEAMS = config.get('competition', 'teams_in_knockout')
YEAR = config.get('competition', 'sr_year')

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
    delay = talk.command_yaml('get-delay "{0}"'.format(original))
    assert delay['units'] == 'seconds'
    delay = timedelta(seconds=delay['delay'])
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

class Match(object):
    def __init__(self, stamp, ident):
        dt = datetime.fromtimestamp(stamp)
        self._when = get_delayed_time(dt)
        self._ident = ident
        self._teams = None

    @property
    def when(self):
        return self._when

    @property
    def ident(self):
        return self._ident

    @property
    def num(self):
        return self._ident[6:]

    @property
    def teams(self):
        if not self._teams:
            teams_data = talk.command_yaml('get-match-teams {0}'.format(self._ident))
            self._teams = teams_data['teams']
        return self._teams

class Schedule(object):
    def __init__(self, schedule):
        self._schedule = [Match(stamp, ident) for ident, stamp in schedule]

    def __iter__(self):
        return iter(self._schedule)

class FilteredSchedule(object):
    def __init__(self, schedule, when_filter = None, team_filter = None):
        self._schedule = schedule
        self._when_filter = when_filter
        self._team_filter = team_filter

    def __iter__(self):
        for match in self._schedule:
            if self._when_filter and not self._when_filter(match.when):
                continue
            if self._team_filter and not self._team_filter(match.teams):
                continue
            yield match

class HTMLSchedule(object):
    def __init__(self, schedule, locations = None):
        self._schedule = schedule
        self._locations = locations

    def to_html_id(self, string):
        # Convert a string into something that could be an html id. Badly.
        return string.strip().lower().replace(' ', '-')

    def get_locations_button(self):
        if self._locations is None:
            return ''

        return '''<script type="text/javascript">
var locations = false;
function toggle_locations(src) {
	sched_tables = document.querySelectorAll("table.match-schedule");
	for (var i=0; i < sched_tables.length; i++) {
		var classes = sched_tables[i].className;
		if (!locations) {
			classes += " locations";
		} else {
			classes = classes.replace('locations', '');
		}
		sched_tables[i].className = classes;
	}
	locations = !locations;
	if (locations) {
		src.textContent = "Hide Locations";
	} else {
		src.textContent = "Show Locations";
	}
}
</script>

<button
	style="cursor: pointer; float: right; margin-right: 20px;"
	onclick="toggle_locations(this)"
	>Show Locations</button>
'''

    def get_header(self, date):
        out = '\n<h2>{0}</h2>'.format(date.strftime('%A, %d %B %Y'))
        return out

    def get_table_head(self):
        out = '\n<table class="match-schedule"><thead><tr>'
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

        clazz = 'team-{0}'.format(team_id)
        if self._locations is not None:
            loc = self._locations[team_id]
            clazz += ' {0}'.format(self.to_html_id(loc))

        return '<td class="{0}">{1}</td>'.format(clazz, text)

    def get_row(self, time, num, teams, show_team_name = False):
        out = '\n<tr class="match-{0}">'.format(int(num))
        cells = [self.get_team_cell(tid, show_team_name) for tid in teams]
        out += "\n\t<td>{0}</td><td>{1}</td>{2}".format(time, num, ''.join(cells))
        out += "\n</tr>"
        return out

    def get_table(self, headings = True, full_names = True, dt_filter = None, team_filter = None):
        date = None
        output = ''

        filtered_schedule = FilteredSchedule(self._schedule, dt_filter, team_filter)
        for match in filtered_schedule:
            dt = match.when
            this_date = dt.date()
            if date != this_date:
                if date is not None:
                    output += self.get_tail()
                date = this_date
                if headings:
                    output += self.get_header(date)
                output += self.get_table_head()
            output += self.get_row(dt.time(), match.num, match.teams, full_names)

        output += self.get_tail()
        return output

    def get_all(self):
        date = None
        output = '<h1>Match Schedule</h1>'
        output += self.get_locations_button()
        output += self.get_table()
        return output
