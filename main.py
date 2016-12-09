from pony.orm import *
from functools import partial
from pprint import pprint
import json
import os

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

    # seed the initial database Event with stupid things
    try:
        with db_session:
            event = Event(name="Terrible ideas hackathon")
            [Vote(event=event, name=n, count=0) for n in (
                "Tinder for pets",
                "Facebook for babies",
                "Giant hamster wheel power generator",
            )]
    except Exception:
        pass

    # seed the rest of the events with more substantial information
    from faker import Faker
    import random
    fake = Faker()
    event_number = 10
    events = [
        {
            "name": "Best {} contest.".format(fake.job()),
        } for _ in range(event_number)
    ]
    for e in events:
        votes = [
            {
                "name": fake.name(),
                "count": random.choice(range(11)),
            } for _ in range(10)
        ]
        # pprint(e)
        # pprint(votes)
        # print('-'*80)
        # seed the database
        for v in votes:
            try:
                with db_session:
                    event = Event.get(**e) if Event.get(**e) else Event(**e)
                    # print(event)
                    vote = Vote(event=event, **v)
            except Exception as exc:
                # print("could not create elements in database")
                # print('Event: {}\nVote: {}'.format(e, v))
                # print(exc)
                continue



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
    event_dict['votes'] = [v.to_dict() for v in Vote.select(lambda v: v.event == event)]
    event_dict['amount'] = len(event_dict['votes'])
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

    votes = [v.to_dict() for v in votes]

    result = {'amount': len(votes), 'votes': votes}

    return json.dumps(result)


@db_session
def get_events():
    """Return a json string of all events."""

    events = [event.to_dict() for event in Event.select()]
    result = {'amount': len(events), 'events': events}
    return json.dumps(result)



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
    return get_event(event_id)


# Set up flask
from flask import Flask, request
import markdown

app = Flask(__name__)


@app.route('/')
def root():
    fp = os.path.join(os.path.dirname(__file__), 'root.md')
    with open(fp) as md:
        msg = md.read()
    return markdown.markdown(msg)


@app.route('/event/', methods=['GET', 'POST'])
def event_root():
    if request.method == 'GET':
        return get_events()
    elif request.method == 'POST':
        name = request.form['name']
        return create_event(name)


@app.route('/event/<int:event_id>', methods=['GET', 'POST', 'DELETE'])
def specific_event(event_id):
    if request.method == 'GET':
        return get_event(event_id)
    elif request.method == 'DELETE':
        return delete_event(event_id)
    elif request.method == 'POST':
        action = request.form['action']
        if action == 'reset':
            return reset(event_id=event_id)


@app.route('/vote/', methods=['GET', 'POST'])
def vote_root():
    if request.method == 'GET':
        return get_votes()
    elif request.method == 'POST':
        event_id = request.form['event_id']
        name = request.form['name']
        return create_vote(name, event_id)


@app.route('/vote/<int:vote_id>', methods=['GET', 'POST', 'DELETE'])
def specific_vote(vote_id):
    if request.method == 'GET':
        return get_vote(vote_id)
    elif request.method == 'DELETE':
        return delete_vote(vote_id)
    # http method is POST, so we increment, decrement, or reset a vote and return the result
    elif request.method == 'POST':
        action = request.form['action']
        if action == 'increment':
            return increment(vote_id)
        elif action == 'decrement':
            return decrement(vote_id)
        elif action == 'reset':
            return reset(vote_id=vote_id)


if __name__ == "__main__":
    # seed()
    app.run()
