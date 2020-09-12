# trello-track

Track running processes on Trello.

Install: `pip install trello-track`

## Why?

Let's say you're running experiments on several machines. Wouldn't it be nice to have an easy way
to see when everything is done and if anything has encountered an error?

`trello-track` addresses this issue by adding checklist items to a Trello card that are updated
to reflect the progress of a process. You can quickly see at a glance where all your experiments
are at!

![Example Trello cards](https://raw.githubusercontent.com/seanmacavaney/trello-track/master/gist.png)

Features:

 - Command line and python interfaces
 - Task status indicators:
   - ⚪ ready
   - ⌛ in progress
   - 🔵 success
   - 🔴 failed
 - Error logging

![Features](https://raw.githubusercontent.com/seanmacavaney/trello-track/master/feats.png)

## How?

There's two interfaces: a command line interface and a Python interface.

They both take the Trello Card ID. This is easy to pluck out of the URL.

![Find the card ID in the URL of the card](https://raw.githubusercontent.com/seanmacavaney/trello-track/master/card_id.png)

### CLI

Format: `trello-track [card-id] [command...]`

Example: `trello-track 9ngUrIZ2 bash train_eval.sh A X 0.1`

### Python

```python
import trello_track

with trello_track.track('do something', card_id='9ngUrIZ2'):
	foo()
```

But you probably don't want to hard-code a card ID, do you? You can instead skip the optional parameter
and provide it via an environment variable:

`TRELLO_CARD=9ngUrIZ2 python ...`

You can also queue up a bunch of tasks to run using `trello_track.TaskManager`:

```python
import trello_track

with trello_track.TaskManager() as tasks:
	tasks.add('foo', foo)
	tasks.add('bar', bar)
	tasks.add('baz', baz)
```

### Authentication

Authentication is done via the Trello API key and token.

You can access your key and generate a token at https://trello.com/app-key.

You then can provide them to your application via the `TRELLO_KEY` and `TRELLO_TOKEN` environment
variables, or encoded as json in `~/.trello` or `./.trello`:

```json
{"key": "XXX", "token": "XXX"}
```
