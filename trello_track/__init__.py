import sys
import json
import os
import platform
import subprocess
import contextlib
import requests


CHECKLIST_NAME = 'Commands'
ICON_READY, ICON_IP, ICON_DONE, ICON_FAIL = '⚪', '⌛', '🔵', '🔴'


_CREDS = None
def CREDS():
    global _CREDS
    if _CREDS is None:
        c = {}
        if os.path.exists(os.path.expanduser('~/.trello')):
            c.update(json.load(open(os.path.expanduser('~/.trello'), 'rt')))
        if os.path.exists('./.trello'):
            c.update(json.load(open('./.trello', 'rt')))
        if 'TRELLO_TOKEN' in os.environ:
            c['token'] = os.environ['TRELLO_TOKEN']
        if 'TRELLO_KEY' in os.environ:
            c['key'] = os.environ['TRELLO_KEY']
        if 'key' not in c or 'token' not in c:
            raise RuntimeError('Missing Trello `key` and `token`. Please provide as JSON in ~/.trello, '
                               './.trello, or as TRELLO_KEY and TRELLO_TOKEN environment vars.\n\n'
                               'You can find your key and generate a token at https://trello.com/app-key')
        _CREDS = c
    return _CREDS


def _api(method, path, params=None):
    C = CREDS()
    params = params or {}
    params = {**params, 'key': C['key'], 'token': C['token']}
    return json.loads(requests.request(method, path, params=params).text)


class TrelloTracker:
    def __init__(self, desc, card_id=None, _start_in_progress=False):
        if card_id is None:
            card_id = os.environ.get('TRELLO_CARD')
        if card_id is None:
            sys.stderr.write('TRELLO: No card supplied. This operation will not be tracked.\n')
            self.state = 'NO_TRACK'
        else:
            # Find card
            matching_cards = _api("GET", "https://trello.com/1/search", {'query': card_id})
            card = None
            for c in matching_cards['cards']:
                if card_id in (c['id'], c['shortLink']):
                    card = c
                    break
            if card is None:
                sys.stderr.write('TRELLO: Could not find card: {}. This operation will not be tracked.\n'.format(card_id))
                self.state = 'NO_TRACK'
            else:
                all_checklists = _api("GET", "https://api.trello.com/1/cards/{id}/checklists".format(**card))
                checklist = [c for c in all_checklists if c['name'] == CHECKLIST_NAME]
                if len(checklist) == 1:
                    checklist = checklist[0]
                else:
                    checklist = _api(
                        "POST",
                        "https://api.trello.com/1/cards/{id}/checklists".format(**card),
                        {'name': CHECKLIST_NAME})
                icon = ICON_IP if _start_in_progress else ICON_READY
                check_item = _api(
                    "POST",
                    "https://api.trello.com/1/checklists/{id}/checkItems".format(**checklist),
                    {'name': '{} {}'.format(icon, desc)})
                self.state = 'IP' if _start_in_progress else 'READY'
                self.desc = desc
                self.card = card
                self.check_item = check_item

    def __enter__(self):
        assert self.state in ('IP', 'READY', 'NO_TRACK')
        if self.state == 'READY':
            _api("PUT",
                 "https://api.trello.com/1/cards/{}/checkItem/{}".format(self.card['id'], self.check_item['id']),
                 {'state': 'complete', 'name': '{} {}'.format(ICON_IP, self.desc)})
            self.state = 'IP'
        return self

    def __exit__(self, ex_type, ex_val, ex_traceback):
        assert self.state in ('IP', 'NO_TRACK')
        if self.state == 'NO_TRACK':
            return
        if ex_type:
            self.state = 'FAIL'
            _api("PUT",
                 "https://api.trello.com/1/cards/{}/checkItem/{}".format(self.card['id'], self.check_item['id']),
                 {'state': 'complete', 'name': '{} {}'.format(ICON_FAIL, self.desc)})
            _api("POST",
                 "https://api.trello.com/1/cards/{id}/actions/comments".format(**self.card),
                 {'text': '{} failed with exception:\n`{}`'.format(self.desc, ex_val)})
        else:
            self.state = 'DONE'
            _api("PUT",
                 "https://api.trello.com/1/cards/{}/checkItem/{}".format(self.card['id'], self.check_item['id']),
                 {'state': 'complete', 'name': '{} {}'.format(ICON_DONE, self.desc)})


@contextlib.contextmanager
def track(desc, card_id=None):
    with TrelloTracker(desc, card_id, _start_in_progress=True) as tracker:
        yield tracker


class TaskManager:
    def __init__(self, card_id=None):
        if card_id is None:
            card_id = os.environ.get('TRELLO_CARD')
        self.card_id = card_id
        self.tasks = []

    def add_task(self, desc, fn):
        self.tasks.append((desc, fn))

    def run(self):
        trackers = []
        for desc, _ in self.tasks:
            trackers.append(TrelloTracker(desc, self.card_id))
        for tracker, (_, fn) in zip(trackers, self.tasks):
            with tracker:
                fn()

    def clear(self):
        self.tasks.clear()

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_val, ex_traceback):
        if ex_type:
            self.run()
            self.clear()


def main_cli():
    main(sys.argv[1:])


def main(argv):
    assert len(argv) >= 2, "usage: [card_id] [command...]"
    card_id, args = argv[0], argv[1:]
    cmd = ' '.join((a if ' ' not in a else f'"{a}"') for a in args)
    with track(card_id=card_id, desc=f'@{platform.node()} `{cmd}`'):
        p = subprocess.Popen(args)
        while True:
            try:
                return_code = p.wait()
                if return_code != 0:
                    raise subprocess.CalledProcessError(return_code, args)
                break
            except KeyboardInterrupt:
                pass



if __name__ == '__main__':
    main_cli()
