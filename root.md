## API

[**API source code**](https://github.com/knowsuchagency/voting-api/blob/master/main.py)

[**API root**](http://voting-bamf.rhcloud.com/)

The database has been seeded with information. 

event/1 is a really simple event with only 3 votes.

All following events have a semi-random name and 10 votes (possibly 9 due to naming conflicts during seeding) with a randomly generated count between 0 and 10.

Any GET request to the database will not change information in the database.

In order to increment, decrement, or reset any specific votes, send a POST request to the appropriate endpoint with the specific action to be performed as a parameter in the form body i.e "action=increment".
Any successful POST request will return the modified object in the request.

Examples using curl are shown below. No authentication is currently required.

### Root url

    curl http://voting-bamf.rhcloud.com/
    
### get all events

    curl http://voting-bamf.rhcloud.com/event/
    
    {
        "amount": 117,
        "events" [...]
    }

### get a specific event
    
    curl http://voting-bamf.rhcloud.com/event/1
    
    {
      "amount": 3,
      "votes": [
        {
          "count": 0,
          "event": 1,
          "id": 2,
          "name": "Facebook for babies"
        },
        {
          "count": 0,
          "event": 1,
          "id": 3,
          "name": "Giant hamster wheel power generator"
        },
        {
          "count": 0,
          "event": 1,
          "id": 1,
          "name": "Tinder for pets"
        }
      ],
      "id": 1,
      "name": "Terrible ideas hackathon"
    }

### get all votes

    curl http://voting-bamf.rhcloud.com/vote/
    
    {
        "amount": 1303,
        "votes" : [...]
    }
    
### get a specific vote

    curl http://voting-bamf.rhcloud.com/vote/1
    
    {
      "count": 0,
      "event": 1,
      "id": 1,
      "name": "Tinder for pets"
    }

### increment a vote

    curl http://voting-bamf.rhcloud.com/vote/1 -d "action=increment"
    
### decrement a vote

    curl http://voting-bamf.rhcloud.com/vote/1 -d "action=decrement"
    
### reset a vote's count to zero

    curl http://voting-bamf.rhcloud.com/vote/1 -d "action=reset"
    
### reset all votes for a particular event

    curl http://voting-bamf.rhcloud.com/event/1 -d "action=reset"
    
### create a new event
note: Event names must be unique. newName is just an example

    curl http://voting-bamf.rhcloud.com/event/ -d "name=newName"

### create a new vote
note: Vote name must be unique for a given Event. newName and event_id=1 are just examples.

    curl http://voting-bamf.rhcloud.com/vote/ -d "name=newName&event_id=1"
    
### delete an event
note: all the event's related votes will be deleted as well.

    curl http://voting-bamf.rhcloud.com/event/2 -X DELETE
    
### delete a vote

    curl http://voting-bamf.rhcloud.com/vote/4 -X DELETE