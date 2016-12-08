from pony.orm import *
from functools import partial
import json

# make all json serializations indent by default
json.dumps = partial(json.dumps, indent=2)

# set up database connection
db = Database()


class Event(db.Entity):
    """
    This class represents an event; a collection of votes.
    """
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    votes = Set('Vote', cascade_delete=True)


class Vote(db.Entity):
    """
    This class represents an individual vote.
    """
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    count = Required(int, default=0)
    event = Required(Event)
    # ensure each vote name is unique per event
    composite_key(event, name)


db.bind("sqlite",
        "db.sqlite",
        # create database if it doesn't exist
        create_db=True
        )
db.generate_mapping(create_tables=True)


def seed():
    """
    Seed the database.
    """

    votes_list = [
        {
            'name': 'Tinder for pets',
            'count': 0,
        },
        {
            'name': 'Giant hamster wheel power generator',
            'count': 0,
        },
        {
            'name': 'Facebook for babies',
            'count': 0,
        },
    ]

    try:
        with db_session:
            event = Event(name="Terrible ideas hackathon")
            votes = [Vote(event=event, **v) for v in votes_list]
    except pony.orm.core.TransactionIntegrityError as e:
        print(e)


# define database transaction functions
@db_session
def increment(vote_id):
    """Increment vote and return json string of that vote"""
    vote = Vote.get(id=vote_id)
    vote.count += 1
    return json.dumps(vote.to_dict())


@db_session
def decrement(vote_id):
    """Decrement vote and return json string of that vote"""
    vote = Vote.get(id=vote_id)
    vote.count -= 1
    return json.dumps(vote.to_dict())


@db_session
def get_event(event_id):
    event = Event.get(id=event_id)
    event_dict = event.to_dict()
    votes_dict_list = [v.to_dict() for v in Vote.select(lambda v: v.event == event)]
    event_dict['votes'] = votes_dict_list
    return json.dumps(event_dict)


@db_session
def get_vote(vote_id):
    """Return the json string of a given vote."""
    return json.dumps(Vote.get(id=vote_id).to_dict())


@db_session
def get_votes(event_id=None):
    """
    Return a json string of votes.

    If no parameter is passed, all votes are returned.
    If an event_id is given, votes will be filtered by the event.
    """
    if event_id is None:
        votes = Vote.select()
    else:
        votes = Vote.select(lambda v: v.event == Event.get(id=event_id))

    return json.dumps([v.to_dict() for v in votes])


@db_session
def get_events():
    """Return a json string of all events."""
    events = []
    for event in Event.select():
        event_dict = event.to_dict()
        votes_dict_list = [v.to_dict() for v in Vote.select(lambda v: v.event == event)]
        event_dict['votes'] = votes_dict_list
        events.append(event_dict)

    return json.dumps(events)

@db_session
def create_event(name):
    event = Event(name=name)
    return json.dumps(event.to_dict())

@db_session
def create_vote(name, event_id):
    vote = Vote(name=name, event=Event.get(id=event_id))
    return json.dumps(vote.to_dict())

@db_session
def delete_event(event_id):
    event = Event.get(id=event_id)
    name = event.name
    event.delete()
    return json.dumps('successfully deleted event: ' + name)

@db_session
def delete_vote(vote_id):
    vote = Vote.get(id=vote_id)
    name = vote.name
    vote.delete()
    return json.dumps('successfully deleted vote: ' + name)


@db_session
def reset(vote_id=None, event_id=None):
    """
    Reset vote counts to 0.

    If a vote id is given, reset that vote's count.
    If an event id is given, reset all the votes for that event.
    Else, all votes are reset.
    """

    # handle individual vote id
    if vote_id is not None:
        # reset vote
        vote = Vote.get(id=vote_id)
        vote.count = 0
        # return vote json
        return get_vote(vote_id)

    # get votes for given event, else all votes
    if event_id is None:
        votes = Vote.select()
    else:
        votes = Vote.select(lambda v: v.event == Event.get(id=event_id))

    # reset votes
    for vote in votes:
        vote.count = 0

    # return json of votes
    return get_votes(event_id=event_id)


# Set up flask
from flask import Flask, request
from textwrap import dedent
import markdown

app = Flask(__name__)


@app.route('/')
def root():
    with open('root.md') as fp:
        return markdown.markdown(fp.read())


@app.route('/vote/', methods=['GET', 'POST'])
@app.route('/vote/<int:vote_id>', methods=['GET', 'POST', 'DELETE'])
def vote_route(vote_id=None):
    # no vote id given, return all votes
    if vote_id is None:
        if request.method == 'GET':
            return get_votes()
        elif request.method == 'POST':
            event_id = request.form['event_id']
            name = request.form['name']
            return create_vote(name, event_id)
    # vote id is given and HTTP verb is GET. return individual vote
    elif request.method == 'GET':
        return get_vote(vote_id)
    # vote id is given and HTTP verb is DELETE
    elif request.method == 'DELETE':
        return delete_vote(vote_id)
    # http method is POST, so we increment, decrement, or reset a vote and return the result
    elif request.method == 'POST':
        action = request.form['action']
        # ensure action is either 'increment', 'decrement', or 'reset'
        if action == 'increment':
            return increment(vote_id)
        elif action == 'decrement':
            return decrement(vote_id)
        elif action == 'reset':
            return reset(vote_id=vote_id)


@app.route('/event/', methods=['GET', 'POST'])
@app.route('/event/<int:event_id>', methods=['GET', 'POST', 'DELETE'])
def event_route(event_id=None):
    # event id is not given so return all events
    if event_id is None:
        if request.method == 'GET':
            return get_events()
        elif request.method == 'POST':
            name = request.form['name']
            return create_event(name)
    # HTTP GET method so return individual event
    elif request.method == 'GET':
        return get_event(event_id)
    # DELETE event
    elif request.method == 'DELETE':
        return delete_event(event_id)
    # reset event
    elif request.method == 'POST':
        action = request.form['action']
        if action == 'reset':
            return reset(event_id=event_id)


if __name__ == "__main__":
    seed()
    app.run()
