
import time  # Times
import sqlite3  # easy and fast SQL
import praw  # simple interface to the reddit API, also handles rate limiting of requests
import re  # REGEX stuff
import sys  # System
import logging # For logging

#$ Setting Basic Logging Config.
logging.basicConfig(filename='quesbot.log', level=logging.DEBUG)


'''USER CONFIGURATION'''

# THIS SET IT A LAYOVER FROM THE "SUBMISSION REPLYBOT" on GitHub and includes login credentials

USERNAME = ""
# This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD = ""
# This is the bot's Password.
USERAGENT = ""
# This is a short description of what the bot does. For example "/u/trip96  Quest"
SUBREDDIT = "questbot"
# This is the sub or list of subs to scan for new posts. For a single sub, use "sub1".
# For multiple subreddits, use "sub1+sub2+sub3+..."
TITLESTRING = ["[QUEST]"]
# These are the words you are looking for in the titles.
MAXPOSTS = 100
# This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
# This is how many seconds you will wait between  FULL cycles. The bot is completely inactive during this time.


# THIS IS For THE DOGETIPBOT and questbot comment CHECKER PROGRAM

user = 'dogetipbot'
self = 'questbot'



# SO I CAN PUBLISH WIHTHOUT LOGIN CREDENTIALS
WAITS = str(WAIT)
try:
    import \
        credentials  # This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials

    USERNAME = credentials.get_username()
    PASSWORD = credentials.get_password()
    USERAGENT = credentials.get_user_agent()
except ImportError:
    pass

print("------------------------------------------------------------------------------------------------")
print("Initializing Program")
print("------------------------------------------------------------------------------------------------")

# SQL Connection

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS quests'
            '(quest_id TEXT, reply_id TEXT, author TEXT, bounty REAL, completed TEXT, champion TEXT, post_full TEXT)')

cur.execute('CREATE TABLE IF NOT EXISTS users'
            '(username TEXT, reputation REAL, xp REAL, level REAL)')

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')

print('Loaded Completed tables')

sql.commit()


#REDDIT LOGIN USING PRAW

print("Attempting Reddit Login")
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)
print("Successfully Logged in to Reddit using credentials")

#SCAN DOGETIPBOT'S COMMENTS FOR TIPS TO QUESTBOT AND LIFT THE VALUE FOR TIPS
#This is the definitions it uses, populated strings using the append function.

previous_posts = []

# Set of Subroutines For scanning Dogetipbots comments

# Getting new Posts for dogetipbot

def get_new_posts(reddit_user):
    posts = [post for post in reddit_user.get_comments() if post not in previous_posts]
    return posts


# For keeping track of dogetipbots comments by adding old posts to the list (array).

def add_previous_posts():
    reddit_user = r.get_redditor(user)
    for previous_post in get_new_posts(reddit_user):
        previous_posts.append(previous_post)  # add old posts to the array


# Dogetipbot Comment Parsing engine for REGEX. Returns cleaner text

def process(text):
    text = text.split(':')[1][1:]
    for x in ['&amp;nbsp;', ['-&gt;', '->'], '^', '_', '^', '[[help]](http']:
        if type(x) is list:
            text = text.replace(x[0], x[1])
        else:
            text = text.replace(x, '')
    return text


# Get QUESTING USER information - Used for grabbing info from the SQL database

def get_user_reputation(pauthor):
    logging.debug("Getting REPUTATION for: " + pauthor)
    for reputation in cur.execute('SELECT reputation FROM users WHERE username="%s"' % pauthor.lower()):
        reputation_value = ("".join(map(str, reputation)))
        logging.debug("REPUTATION is: " + reputation_value)
        return reputation_value


def get_user_level(pauthor):
    logging.debug("Getting LEVEL for: " + pauthor)
    for level in cur.execute('SELECT level FROM users WHERE username="%s"' % pauthor.lower()):
        level_value = ("".join(map(str, level)))
        logging.debug("LEVEL is: " + level_value)
        return level_value


def get_user_xp(pauthor):
    logging.debug("Getting XP for: " + pauthor)
    for xp in cur.execute('SELECT xp FROM users WHERE username="%s"' % pauthor.lower()):
        xp_value = ("".join(map(str, xp)))
        logging.debug("XP Value is: " + xp_value)
        return xp_value


def get_quest_author(bounty_id):
    logging.debug("Getting QUEST AUTHORr for: " + bounty_id)
    for author in cur.execute('SELECT author FROM quests WHERE quest_id="%s"' % bounty_id):
            qauthor = ("".join(map(str, author)))
            logging.debug("Quest Author is: " + qauthor)
            return qauthor


def get_link_id(bounty_id):
    logging.debug("Getting Link ID for: " + bounty_id)
    for linkid in cur.execute('SELECT reply_id FROM quests WHERE quest_id="%s"' % bounty_id):
            reply_id = ("".join(map(str, linkid)))
            logging.debug(" REPLY LINK ID is: " + reply_id)
            return reply_id


def get_bounty(bounty_id):
    logging.debug("Getting BOUNTY for: " + bounty_id)
    for bounty in cur.execute('SELECT bounty FROM quests WHERE quest_id="%s"' % bounty_id):
            bounty_value = ("".join(map(str, bounty)))
            logging.debug("Bounty is: " + bounty_value)
            return bounty_value


def get_quest_completed(bounty_id):
    logging.debug("Getting COMPLETION STATUS for: " + bounty_id)
    for completed in cur.execute('SELECT completed FROM quests WHERE quest_id="%s"' % bounty_id):
            quest_completed = ("".join(map(str, completed)))
            logging.debug("QUEST COMPLETION STATUS is: " + quest_completed)
            return quest_completed


## SET FLAIRS


def set_flair_complete(bounty_id):
    logging.debug("Setting Flair status to COMPLETE")
    cur.execute('SELECT post_full FROM quests WHERE quest_id="%s"' % bounty_id)
    post_full = ("".join(map(str, cur.fetchone())))
    flair_post = r.get_submission(url=post_full)
    flair_post.set_flair(flair_text="COMPLETED", flair_css_class="completed")
    logging.debug("Flair Status has successfully been changed to COMPLETE")


def set_flair_available(post_full):
    logging.debug("Setting Flair status to Available")
    flair_post = r.get_submission(url=post_full)
    flair_post.set_flair(flair_text="Available", flair_css_class="available")
    logging.debug("Flair status has successfully been changed to COMPLETE")



# Function to Add original quest_id to table (used for keeping a live and updated balance later on)

def get_quest_reply_id(pid):
    logging.debug("Attempting to retrieve and insert into database reply_id (link) for quest " + pid + "...")
    print("Attempting to retrieve and insert into database reply_id (link) for quest " + pid + "...")
    pid = str(pid)
    reddit_self = r.get_redditor(self)
    try:
        for post in get_new_questbot_post_id(reddit_self):
            reply_id = post.permalink
            cur.execute("UPDATE quests SET reply_id='%s' WHERE quest_id='%s' " % (reply_id, pid))
            sql.commit()
            print("Successfully inserted reply_id into quests table. Now 30 Sec PRAW refresh WAIT")
            logging.debug("Successfully inserted reply_id into quests table. Now 30 Sec PRAW refresh WAIT")
            time.sleep(31)  # has to be longer than 30 seconds due to PRAW limitations.
            logging.debug("PRAW WAIT OVER, moving on...")

    except praw.errors.RateLimitExceeded as err:
        print("Rate Limit Exceeded:\n" + str(err), sys.stderr)


# Get last Comment QUESTBOT made for getting the UPDATE LINK (aka link_id) (USES 30 sec sleep for PRAW Cache refresh)

def get_new_questbot_post_id(reddit_self):
    newpost = [post for post in reddit_self.get_comments(sort='new', limit=1)]
    return newpost


# Update Balances function

def update_balances(tip_id, tip_value):
    print("Updating Quest Balances...")
    logging.debug("Updating Quest Balances...")

    # search the database for the tip_id and then retrieve the existing bounty

    for bounty_value in cur.execute('SELECT bounty FROM quests WHERE quest_id="%s"' % tip_id):
        old_bounty_value = float("".join(map(str, bounty_value)))
        logging.debug("Old Bounty Value is : " + str(old_bounty_value))

        # Then add the bounty to the tip_value

        new_bounty_value = float(float(old_bounty_value) + float(tip_value))
        logging.debug("NEW Bounty Value is : " + str(new_bounty_value))

        # Then commit the new bounty to the database

        cur.execute("UPDATE quests SET bounty='%f' WHERE quest_id='%s' " % (float(new_bounty_value), tip_id))
        logging.debug("Committed new bounty value to DB")

        time.sleep(3)

        # Then update the original comment with the new bounty

        for rid in cur.execute('SELECT reply_id FROM quests WHERE quest_id="%s"' % tip_id):
            reply_id = ("".join(map(str, rid)))
            reply_post = r.get_submission(url=reply_id).comments[0]

            rex = re.compile(r'Ð(\d+\.?\d*)')
            doge_value = (rex.findall(reply_post.body))
            old_bounty_value = ("".join(map(str, doge_value)))

            updated_quest_post = str(reply_post.body.replace(str('Ð'+old_bounty_value), str('Ð'+str(new_bounty_value))))

            print("Updating Quest Post Balance")
            logging.debug("Updating NEW value into Quest Created Post")
            reply_post.edit(updated_quest_post)
            print("Update Successful")
            logging.debug("Update Successful")
            time.sleep(3)
    sql.commit()



#Scan for Questbot commands in the subreddits

def scan_for_commands():
    print('Searching ' + SUBREDDIT + ' for Questbot Commands.')
    logging.debug('Searching ' + SUBREDDIT + ' for Questbot Commands.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=100)

    ## Check posts and keep track of previous posts

    for post in posts:
        pid = post.id
        bounty_id = post.link_id.replace("t3_", "")
        command_author = str(post.author)
        pauthor = post.author.name
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
            pbody = post.body.lower()
            post_body = str("".join(map(str, pbody)))

            ## Check to see if questbot is mentioned and pull the comment

            if "+/u/questbot " in post_body:
                print("Questbot has recognized its being called")
                logging.debug("Questbot has recognized its being called")
                rex = re.compile('\+/u/questbot\s(\w+)')
                questbot_command = ("".join(map(str, (rex.findall(pbody)))))

                ## Process the command using the function
                logging.debug("Passing information into PROCESS COMMAND FUNCTION")
                process_command(questbot_command, bounty_id, pbody, command_author, post, pauthor)
    time.sleep(3)

sql.commit()


#Process User Commands


def process_command(questbot_command, bounty_id, pbody, command_author, post, pauthor):

    quest_completed = get_quest_completed(bounty_id)
    quest_author = get_quest_author(bounty_id)
    bounty_value = get_bounty(bounty_id)
    reply_id = get_link_id(bounty_id)

    if str(questbot_command) == "complete":
        print("COMPLETE call has been made and recognized")
        logging.debug("COMPLETE call has been made and recognized")
        if str(quest_completed) != "YES":

            #set and send the message notifying the author

            msg = str("/u/" + command_author + " is seeking completion for your quest located here: " + reply_id +
            "\n\n *** \n\n You can reward this person by issuing this command under the Quest Post: \n\n"
            "**+/u/questbot reward " + command_author + "**")
            r.send_message(quest_author, "Questbot", msg)

        elif str(quest_completed) == "YES":
            post.reply("Quest already completed!")
            logging.debug("Quest is already complete")


    # Check for reward command

    elif str(questbot_command) == "reward":
        print("REWARD call made and recognized")
        logging.debug("REWARD call made and recognized")

        # Pull out user name for tipping from post after the word "reward."

        rex = re.compile(r'reward\s(\w+)')
        reward_user_name = ("".join(map(str, (rex.findall(pbody)))))

        ## If issuing user matches the quest author from database use dogetipbot to send reward
        ## Also checking to see if quest has been completed yet by comparing to database

        if str(command_author) == str(quest_author) and str(quest_completed) != "YES":

            ##Make quest completed in the database
            logging.debug("Updating database to COMPLETE")

            cur.execute("UPDATE quests SET completed='%s' WHERE quest_id='%s' " % ("YES", bounty_id))
            sql.commit()

            ## Reply with the congrats and the reward tip.
            logging.debug("Posting The Reward TIP post to :" + reward_user_name + ". With a value of: " + bounty_value)
            post.reply("Quest **" + str(bounty_id) + "** Complete! Congratulations "
                       "**" + str(reward_user_name) + "** on becoming the **Champion** of this quest. "
                       "\n\n **Here is your reward!** \n\n *** \n\n +/u/dogetipbot @" + str(reward_user_name) +
                       " " + bounty_value + " doge verify \n\n *** \n\n"
                       "^If ^you ^like ^Questbot ^please ^donate ^to: ^DDwsRDCkJto6eRRUEewVhgXWXEDRiy47L4 ^or ^tip ^/u/trip96")

            ## Update Original Post with completed message
            logging.debug("Passing Into QUEST COMPLETE function")
            quest_complete(bounty_id, reward_user_name,
                           bounty_value, pauthor)

        elif str(command_author) == str(quest_author) and str(quest_completed) == "YES":
            post.reply("Quest already completed!")
            logging.debug("Quest already completed")

        elif str(command_author) != str(quest_author) and str(quest_completed) != "YES":
            post.reply("You are not the Quest Giver and cannot issue rewards on this quest!")
            logging.debug("Cannot issue reward because user is NOT the Quest Author. Posting message.")

sql.commit()


# Quest Completed Function


def quest_complete(bounty_id, reward_user_name, bounty_value, pauthor):
    print("Updating Quest Balances FOR COMPLETION...")
    logging.debug("Updating Quest Balances FOR COMPLETION...")

    # Update Quest Giver Stats

    qg_reputation_new = float(float(get_user_reputation(pauthor))+1)
    cur.execute('UPDATE users SET reputation="%d" WHERE username="%s"' % (qg_reputation_new, pauthor.lower()))
    sql.commit()

    logging.debug("Updating Quest giver stats reputation is now: " + str(qg_reputation_new))

    # Update user stats for user who completed quest

    logging.debug("Finding Quest Champion in DB.")
    cur.execute('SELECT * FROM users WHERE username="%s"' % reward_user_name.lower())
    data = cur.fetchone()
    if data is None:
        logging.debug("Champion NOT already in DB. Adding Now.")
        cur.execute('INSERT INTO users (username, xp, reputation, level) VALUES '
                            '(?,?,?,?)', (reward_user_name.lower(), 1, 0, 0))
        sql.commit()
        time.sleep(2)
    else:
        logging.debug("Champion IS in DB, Updating XP Now.")
        new_user_xp = float(float(get_user_xp(pauthor=reward_user_name.lower()))+1)
        cur.execute('UPDATE users SET xp="%d" WHERE username="%s"' % (new_user_xp, reward_user_name.lower()))
        sql.commit()
        time.sleep(2)

        # search the database for the bounty_id and then replace the post with a quest completed message.

    user_xp = get_user_xp(reward_user_name)

    logging.debug("Champions NEW xp is: " + user_xp)
    logging.debug("Getting the REPLY_ID from DB")

    cur.execute('SELECT reply_id FROM quests WHERE quest_id="%s"' % bounty_id)
    reply_id = ("".join(map(str, cur.fetchone())))
    logging.debug("REPLY_ID is: " + reply_id + " \n Attempting to POST QUEST COMPLETED POST")
    reply_post = r.get_submission(url=reply_id).comments[0]

    quest_completed_post = ("**This Quest is Completed! Congratulations to: " + reward_user_name + "!** \n"
                            "\n\n *** \n\n"
                            "\n Total Bounty | Quest Champion | Champion Total XP \n"
                            ":--------------:|:--------------:|:---------------------:\n"
                            " **Ð" + str(bounty_value) + "** | " + reward_user_name + " | " + str(user_xp) + " "
                            "\n\n *** \n\n ^If ^you ^like ^Questbot ^please ^donate ^to: ^DDwsRDCkJto6eRRUEewVhgXWXEDRiy47L4 ^or ^tip ^/u/trip96")

    reply_post.edit(quest_completed_post)
    print("Successfully Completed updates for completion")
    logging.debug("Successfully Completed updates for completion")
    set_flair_complete(bounty_id)
    time.sleep(3)
sql.commit()



# Scan DOGETIPBOT Comments for tips to Questbot

def scan_tipbot():
    print("Now Checking Dogetipbot Comments for new tips for Questbot...")
    logging.debug("Now Checking Dogetipbot Comments for new tips for Questbot...")
    try:
        reddit_user = r.get_redditor(user)
        for previous_post in get_new_posts(reddit_user):
            link_id = previous_post.link_id
            tip_id = link_id.replace("t3_", "")

            # here we wrap the digits because we only want the numbers not the symbol returned

            rex = re.compile(r'Ð(\d+\.?\d*)')       # Try this!  \d+\.?\d*   # rex = re.compile(r'Ð(\d+)')
            doge_value = (rex.findall(previous_post.body))
            tip_value = float("".join(map(str, doge_value)))

            #Checking For tips to Questbot

            if "-> /u/questbot " in process(previous_post.body):
                print("Found a New Tip For Questbot!")
                logging.debug("Found a New Tip For Questbot!")
                update_balances(tip_id, tip_value)
                time.sleep(3)

            previous_posts.append(previous_post)
        print("Finished Scanning Dogetipbot Comments")
        logging.debug("Finished Scanning Dogetipbot Comments")
        time.sleep(5)
    except praw.errors.RateLimitExceeded as err:
        print("Rate Limit Exceeded:\n" + str(err), sys.stderr)


#SCAN THE SUBREDDIT FOR QUEST POSTS

def scan_sub_posts():
    print('Searching ' + SUBREDDIT + ' for New Quest Posts...')
    logging.debug('Searching ' + SUBREDDIT + ' for New Quest Posts...')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        pid = post.id
        post_full = post.permalink
        try:
            pauthor = post.author.name
        except AttributeError:
            pauthor = '[DELETED]'
        cur.execute('SELECT * FROM quests WHERE quest_id="%s"' % pid)
        if not cur.fetchone():
            # Set Original Bounty to zero
            bounty = 0.0
            pbody = post.selftext.lower()
            pbody += ' ' + post.title.lower()
            if any(key.lower() in pbody for key in TITLESTRING):
                print('Quest post Found! Creating quest with quest_id ' + pid + ' by ' + pauthor)
                logging.debug('Quest post Found! Creating quest with quest_id ' + pid + ' by ' + pauthor)

                # Add the Quest to the Quests table in SQL

                cur.execute('INSERT INTO quests (quest_id, author, bounty, completed, post_full) VALUES '
                            '(?,?,?,?,?)', (pid, pauthor, bounty, "NO", post_full))
                sql.commit()

                # Fetch Quest Giver data from SQL if available
                # IF DATA IS 0 IT means no user in database so lets add them

                cur.execute('SELECT * FROM users WHERE username="%s"' % pauthor.lower())
                data = cur.fetchone()
                if data is None:
                    cur.execute('INSERT INTO users (username, xp, reputation, level) VALUES '
                            '(?,?,?,?)', (pauthor.lower(), 0, 0, 0))
                    sql.commit()
                else:
                    pass

                # Make the Quest Created Comment

                logging.debug("Making QUEST created POST NOW.")
                post.add_comment("**New Quest Created! Comment and Participate Below.** [*What is This?*](http://www.reddit.com/r/questbot/wiki/index) \n\n"
                                "\n *** \n"
                                "\n Current Bounty | Quest Giver (QG) | QG Reputation | Quest ID"
                                "\n:----------------:|:------------:|:------------:|:-------:"
                                "\n **Ð" + str(bounty) + "** | " + pauthor + " | " + str(get_user_reputation(pauthor)) + " | " + pid + " "
                                "\n\n***\n\n"
                                "\n [ ^[Share ^this ^Quest] ](http://www.reddit.com/message/compose?subject=Quest%20Time"
                                "&message=A%20Quester%20Wants%20To%20share%20a%20quest%20with%20you%21%0ACheck%20it%20out%20here%3A%20" + str(post_full) + ")"
                                "\n [ ^[Accept ^this ^Quest] ](http://www.reddit.com/message/compose?to=" + pauthor + "&subject=I%20Accept%20Your%20Quest"
                                "&message=I%20have%20accepted%20your%20quest%20located%20here%3A%20" + str(post_full) + ")"
                                "\n [ ^[Message ^the ^Quest ^Giver] ](http://www.reddit.com/message/compose?to=" + pauthor + "&subject=Concerning%20Quest%3A%20" + pid + ")"
                                "\n\n *^Tip ^this ^comment ^to ^add ^to ^the ^bounty ^USE ^VERIFY ^- ^All ^commands ^must ^be ^issued ^below ^this ^post*\n")


                # Look for the post just created and add th URL of the quest reply post to quests Table
                time.sleep(5)
                get_quest_reply_id(pid)
                set_flair_available(post_full)

                time.sleep(3)

    print("Finished Searching " + SUBREDDIT)
    logging.debug("Finished Searching " + SUBREDDIT)
    time.sleep(3)
    sql.commit()


# Add EXISTING dogetipbot potsts and questbot posts the initial Array

print("------------------------------------------------------------------------------------------------")
print("Populating History Arrays")
print("------------------------------------------------------------------------------------------------")

logging.debug("------------------------------------------------------------------------------------------------")
logging.debug("Populating History Arrays")
logging.debug("------------------------------------------------------------------------------------------------")
add_previous_posts()
print("Added Existing dogetipbot posts to history")

# Main Program Loop

print("------------------------------------------------------------------------------------------------")
print("Starting Main Functions and Main Loop")
print("------------------------------------------------------------------------------------------------")

logging.debug("------------------------------------------------------------------------------------------------")
logging.debug("Starting Main Functions and Main Loop")
logging.debug("------------------------------------------------------------------------------------------------")

while True:
    try:
        scan_sub_posts(), scan_tipbot(), scan_for_commands()
    except Exception as e:
        print('An error has occured:', e)
    print("------------------------------------------------------------------------------------------------")
    print('Finished Cycle! Running again in ' + WAITS + ' seconds ')
    print("------------------------------------------------------------------------------------------------")

    logging.debug("------------------------------------------------------------------------------------------------")
    logging.debug('Finished Cycle! Running again in ' + WAITS + ' seconds ')
    logging.debug("------------------------------------------------------------------------------------------------")
    sql.commit()
    time.sleep(WAIT)