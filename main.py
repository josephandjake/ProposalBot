# -*- coding: utf-8 -*-
import settings

import praw
import random
import time
import cPickle as pickle


class Proposal:
    def __init__(self, title, date, author, contents, comment):
        self.title = title
        self.date = date
        self.author = author.name
        self.contents = contents
        self.status = 1
        self.comment = comment.permalink

    def update_status(self, status):
        # 1 = Processed and added comment
        # 2 = Enough votes to be processed for approval/rejection
        # 3 = Approved, this is now law
        # 4 = Rejected, this is not law
        self.status = status
    def update_date_completed(self):
        self.completed = time.time()
    def update_contents(self, contents):
        self.contents = contents


try:
    proposal_container = pickle.load(file('proposal_container.obj','rb'))
    print "Loaded container from file"
except:
    proposal_container = []
    print "Generated new container"

r = praw.Reddit(user_agent=settings.REDDIT_USERAGENT)

# Move to settings.py?
proposal_keywords = ['PROPOSAL'] 

# Check and update Proposals
def check_and_update_proposals():
    r.login(settings.REDDIT_USER, settings.REDDIT_PASSWORD)
    print "Authenticated"

    # Pull the newest 100 posts on the defined REDDIT_PROPOSAL_SUBREDDIT
    submissions = r.get_subreddit(settings.REDDIT_PROPOSAL_SUBREDDIT).get_new(limit=100)
    
    # Loop through the submissions
    for x in submissions:
        print "Processing submission", x.id
        
        # Check the title for proposal keywords so that this function
        #   only processes topics that are creating a new proposal.
        # This will allow us to remove/call a revote on 
        #   already existing proposals.
        title = x.title
        if any(string in title for string in proposal_keywords):
                
            # This block of code iterates over existing proposals
            #    and populates variables if x is already processed.
            status = 0
            pretty_itty = -1
            for proposal in proposal_container:
                pretty_itty += 1
                # What if the proposal wasn't voted in the same day as the submission was posted?
                if proposal.date == x.created_utc:
                    print x.id, "is already on the system as status", proposal.status
                    status = proposal.status
                    proposal_object = proposal
            #
            
            # This block runs if the proposal has never been
            #    processed before.
            if status == 0:
                print x.id, "has never been processed before."
                
                # Create a comment on this post using
                #     REDDIT_PROPOSAL_COMMENT as source. 
                comment = x.add_comment(settings.REDDIT_PROPOSAL_COMMENT)
    
                print "Added comment", comment.id, "to", x.id
                
                # Create a proposal instance and append it
                #    to the list of exisiting proposals.
                proposal_container.append(Proposal(x.title, x.created_utc, x.author, x.selftext, comment))
                print "Created Proposal instance and added to container"
    
            # This block runs if the proposal has been
            #    processed before but hasn't been rejected
            #    or approved yet.
            if status == 1:
                # Update the proposal contents for this
                #    proposal instance
                proposal_object.update_contents(x.selftext)
                print "Updated Proposal contents"
    
                # A hack to get the original 'please vote'
                #   comment by the bot
                s = r.get_submission(proposal_object.comment)
                s = s.comments[0]
    
                # Reset values between each iteration.
                vote_yes = vote_no = 0
    
                # Populate vote_once from the
                #    ALLOWED_VOTERS variable
                vote_once = settings.ALLOWED_VOTERS
    
                # Iterates over the replies to the
                #    'please vote' comment and counts votes.
                for reply in s.replies:
    
                    # Disallows if not in vote_once list.
                    if reply.author.name in vote_once:
    
                        # Removes name if voted once, preventing dupes.
                        vote_once.remove(reply.author.name)
    
                        # If they include 'yes' anywhere in their reply
                        #    iterate vote_yes by 1.
                        if 'yes' in reply.body:
                            vote_yes += 1
    
                        # If they include 'no' anywhere in their reply
                        #    iterate vote_no by 1.
                        if 'no' in reply.body:
                            vote_no += 1
    
                print "Counted the votes"
    
                # Process the counted votes if there is no one else
                #     left to vote.
                if not vote_once:
                    print "Vote complete"
    
                    # If there are more 'yes' than 'no'.
                    if vote_yes > vote_no:
                        print "Proposal Approved, ", str(vote_yes) + ":" + str(vote_no)
                        
                        # Update comment to reflect the result.
                        s.edit(settings.REDDIT_PROPOSAL_COMMENT_APPROVED % (str(vote_yes), str(vote_no)))
                        
                        # Update the proposal instance to reflect the result.
                        proposal_object.update_status(3)
                        proposal_object.update_date_completed()
                    # If there are more 'no' than 'yes'.
                    if vote_no > vote_yes:
                        print "Proposal Rejected, ", str(vote_no) + ":" + str(vote_yes)
                        
                        # Update the comment to reflect the result.
                        proposal_object.update_status(3)
                        proposal_object.update_date_completed()
    
                        # Update the proposal instance to reflect the result.
                        s.edit(settings.REDDIT_PROPOSAL_COMMENT_REJECTED % (str(vote_no), str(vote_yes)))
                    # Update the proposal instance
                    proposal_container[pretty_itty] = proposal_object
                else:
                    print "Incomplete vote, unable to decide"
    
            # End of processing
            print "Sleeping for 100s"
            time.sleep(100)
            print "Pickling data to file"
            prop_obj = open( "proposal_container.obj", "wb" )
            pickle.dump(proposal_container, prop_obj)
            prop_obj.close()
            


def populate_wiki():
    r.login(settings.REDDIT_USER, settings.REDDIT_PASSWORD)
    print "Authenticated"

    # Take the Proposal list and produce relevant wiki pages.
    text_to_wiki = settings.PROPOSAL_WIKI_HEADER
    for proposal in proposal_container:
        if proposal.status == 3:
            # Create proposal wiki page
            wiki_page = settings.PROPOSAL_WIKI_PAGE_LAYOUT % (proposal.title, proposal.author, str(int(proposal.date)), proposal.contents)
            r.edit_wiki_page(settings.REDDIT_MAIN_SUBREDDIT, settings.PROPOSAL_IDENTIFIER + str(int(proposal.date)), wiki_page)
            # Generate index for main wiki
            generate_url = settings.PROPOSAL_WIKI_URL_LAYOUT % (settings.REDDIT_MAIN_SUBREDDIT, settings.PROPOSAL_IDENTIFIER, str(int(proposal.date)))
            print generate_url
            text_to_wiki += settings.PROPOSAL_WIKI_TEMPLATE % (proposal.title, proposal.author, str(int(proposal.date)), generate_url)
    r.edit_wiki_page(settings.REDDIT_MAIN_SUBREDDIT, settings.PROPOSAL_WIKI_PAGE, text_to_wiki)

def populate_allowed_voters():
    r.login(settings.REDDIT_USER, settings.REDDIT_PASSWORD)
    print "Authenticated"

    target = r.get_subreddit(settings.REDDIT_PROPOSAL_SUBREDDIT)
    approved = target.get_contributors(limit=None)
    for i in approved:
        settings.ALLOWED_VOTERS.append(i.name)
    print "Allowed Voters:", settings.ALLOWED_VOTERS

populate_allowed_voters()
check_and_update_proposals()
populate_wiki()
