# Proposals Bot
A Reddit bot to automagically handle the administration of proposals and laws in a subreddit.

## The Good
* It works as expected.
* Populates allowed voters from approved submitters.
* Keeps track of new proposals.
* Handles, counts, and returns the result of votes on each proposal.
* Updates the wiki to reflect new approved proposals.

## The Bad
* Uses a flat file (pickled) database. If this were to scale that would get very unwieldy.
* No handling of inserted markdown in a proposal.

## Coming soon
* Weekly post of approved proposals to main subreddit.
* Better handling of inserted markdown in a proposal.
* Implement a database layer that hooks into PostGreSQL instead of a flat file database.
