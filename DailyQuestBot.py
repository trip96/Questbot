__author__ = 'Jordan'


import time  # Times
import sqlite3  # easy and fast SQL
import praw  # simple interface to the reddit API, also handles rate limiting of requests
import re  # REGEX stuff
#import sys  # System
import logging  # For logging
import random

#$ Setting Basic Logging Config.
logging.basicConfig(filename='dailyquest.log', level=logging.DEBUG)

'''USER CONFIGURATION'''

# THIS SET IT A LAYOVER FROM THE "SUBMISSION REPLYBOT" on GitHub and includes login credentials

USERNAME = "dailyquestbot"
# This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD = "b1gbxf34"
# This is the bot's Password.
USERAGENT = "For daily quests in the /r/questbot forum."
# This is a short description of what the bot does. For example "/u/trip96  Quest"
SUBREDDIT = "questbot"
# This is the sub or list of subs to scan for new posts. For a single sub, use "sub1".
# For multiple subreddits, use "sub1+sub2+sub3+..."

# Starting Program

print("------------------------------------------------------------------------------------------------")
print("Initializing Program")
print("------------------------------------------------------------------------------------------------")

# SQL Connection

sql = sqlite3.connect('dailyquestbot.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS new_users'
            '(username TEXT, recruit INT)')

cur.execute('CREATE TABLE IF NOT EXISTS users_completed'
            '(daily_recruit TEXT)')

cur.execute('CREATE TABLE IF NOT EXISTS daily_recruit'
            '(quest_id TEXT, post_url TEXT, bounty REAL)')

print('Loaded Completed tables')

sql.commit()


#REDDIT LOGIN USING PRAW

print("Attempting Reddit Login")
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)
print("Successfully Logged in to Reddit using credentials")

self = "dailyquestbot"
previous_comments = []
quest_id = ""
post_deleted = "NO"
time_left = 0
wick = 100


def count_down():
    global post_deleted
    global time_left
    time_left = (time_left - 30)
    if (time_left <= 36000) and (post_deleted == "NO"):
        print("Deleting last DAILY")
        delete_last_post()
        print("Clearing users Table")
        cur.execute('DELETE FROM users_completed')
        sql.commit()
        post_deleted = "YES"
        time.sleep(2)
    elif time_left <= 0:
        print("BOOM Time's UP NEW DAILY NOW!")
        print("Creating NEW DAILY")
        create_recruit_post()
        time.sleep(2)
        time_left = (72000 + wick)
        post_deleted = "NO"
    else:
        print("Time left until new Daily Post: " + str(trunc(float(time_left/3600)) + " hours."))
        pass


def trunc(f):
    ##Truncates/pads a float f to n decimal places without rounding
    slen = len('%.*f' % (1, f))
    return str(f)[:slen]

def update_daily_timer():
    global quest_id
    try:
        post = r.get_submission(submission_id=quest_id)
        reply_post = post.selftext


        rex = re.compile(r'Daily:\s(\d+\.?\d*)')
        time_value = (rex.findall(str(reply_post)))
        old_time_value = ("".join(map(str, time_value)))
        new_time_value = str(trunc(float(time_left/3600)-10))

        updated_quest_post = str(reply_post.replace(str('Daily: '+old_time_value), str('Daily: '+str(new_time_value))))

        print("Updating Daily Timer")
        logging.debug("Updating NEW value into Daily Post")
        post.edit(updated_quest_post)
        print("Update Successful")
        logging.debug("Update Successful")
    except:
        pass


# Make new Daily recruit post


def create_recruit_post():
    try:
        print('Creating Recruit Post')
        recruit_body = open('recruit_body.txt', 'r')
        submission = r.submit('questbot', 'Daily Recruit for (' + time.strftime("%x") + ') - Total Rewards [2000 Doge]', text=recruit_body.read())
        recruit_body.close()
        global quest_id
        quest_id = submission.id
        post_url = submission.url
        cur.execute('INSERT INTO daily_recruit (quest_id, post_url, bounty) VALUES (?,?,?)', (quest_id, post_url, 2000,))
        global wick
        wick = random.randint(0, 21600)
        print("Wick is set to: " + str(wick))
        sql.commit()
        time.sleep(2)
        print("Setting Flair to Daily")
        submission.set_flair(flair_text="Daily", flair_css_class="daily")
        print("Adding First Comment")
        submission.add_comment('**Read Instructions in the above post and issue your *complete* commands below this (reply to this comment).**'
                               ' Your complete comments wil look like this: \n\n '
                               '+/u/dailyquestbot daily recruit complete. */u/yourusername* brought '
                               '*/u/friendsusername* with quest ID: *quest_id_of_newly_created_quest*')

        cur.execute('INSERT INTO users_completed (daily_recruit) VALUES(?)', (self,))
        sql.commit()
        time.sleep(2)
    except:
        pass

def check_recruit_completes(quest_id):
    print('Checking If recruits are complete')
    time.sleep(2)
    cur.execute('SELECT post_url FROM daily_recruit WHERE quest_id="%s"' % quest_id)
    post_url = str("".join(map(str, cur.fetchone())))
    try:
        comment_list = r.get_submission(url=post_url).comments[0]
        comment = comment_list.replies
        scan_for_commands(get_new_comments(comment))
    except:
        pass

    print("Finished Checking Recruit Complete")
    time.sleep(2)


def process_verify_recruit(verify_id, user_recruit):
    print('Verifying Recruit Post')
    verified = "NO"
    try:
        newpost = r.get_submission(submission_id=verify_id)
        questbot_comment = str(newpost.comments[0].body)
        logging.debug(str(questbot_comment))
        if str(user_recruit.lower()) in str(questbot_comment).lower():
            rex_user_reward = re.compile(r'Ð(\d+\.?\d*)')
            user_reward = ("".join(map(str, (rex_user_reward.findall(str(questbot_comment))))))
            if float(user_reward) > 1000:
                print("NEW RECRUIT FOUND! Thanks!")
                verified = 'YES'
                return verified
            else:
                print("Not big enough Tip")
        else:
            print("Not the right user posted this quest")
        print(verified)
    except:
        print("NO POST FOUND")



def get_new_comments(comment):
    posts = [post for post in comment if post not in previous_comments]
    return posts


def scan_for_commands(comment_list):
    print('Scanning for Commands')
    for comment in comment_list:
        command_author = str(comment.author)
        print(comment.author)
        previous_comments.append(comment)
        cur.execute('SELECT * FROM users_completed WHERE daily_recruit=?', (command_author,))
        command_author_test = cur.fetchone()
        if command_author_test is not None:
            print("Author is found in database")
            if command_author == self:
                print("Author is SELF")
                pass
            else:
                print("Letting author know they have completed quest.")
                comment.reply("You have already completed today's daily.")
        else:
            print("AUTHRO NOT FOUND IN DB")
            cur.fetchone()
            body = comment.body.lower()
            post_body = str("".join(map(str, body)))

            ## Check to see if questbot is mentioned and pull the Information

            if "+/u/dailyquestbot daily recruit complete. " in post_body:

                print("Daily Recruit Command Recognized")
                rex_user_reward = re.compile('\scomplete\.\s/u/(\w+)')
                user_reward = ("".join(map(str, (rex_user_reward.findall(body)))))
                rex_user_recruit = re.compile('\sbrought\s/u/(\w+)')
                user_recruit = ("".join(map(str, (rex_user_recruit.findall(body)))))
                rex_verify_url = re.compile('\sid:\s(\w+)')
                verify_id = ("".join(map(str, (rex_verify_url.findall(body)))))

                if process_verify_recruit(verify_id, user_recruit) == "YES":
                    give_daily_tip(quest_id, command_author, user_reward, comment)
                else:
                    comment.reply("There was an error with your submission, Try again.")
    print("finished scanning for commands!.")
    time.sleep(2)

sql.commit()


def give_daily_tip(quest_id, command_author, user_reward, comment):
    print("Giving out a daily Tip Now!")
    cur.execute('INSERT INTO users_completed (daily_recruit) VALUES(?)', (command_author,))
    cur.execute('INSERT INTO new_users (username) VALUES(?)', (user_reward,))
    sql.commit()
    cur.execute('SELECT bounty FROM daily_recruit WHERE quest_id ="%s"' % quest_id)
    total_reward = str("".join(map(str, cur.fetchone())))
    reward_amount = float(total_reward) * 0.1
    new_reward_amount = float(total_reward) - float(reward_amount)
    cur.execute('UPDATE daily_recruit SET bounty="%f" WHERE quest_id="%s"' % (float(new_reward_amount), quest_id))
    sql.commit()
    try:
        comment.reply("**Congratulations on fulfilling today's Daily Recruit Quest.** \n"
                  "Here is your reward: +/u/dogetipbot " + str(reward_amount) + " doge verify.")
    except:
        pass


def delete_last_post():
    global quest_id
    try:
        delete_post = r.get_submission(submission_id=quest_id)
        delete_post.delete()
    except:
        pass

create_recruit_post()

while True:

    check_recruit_completes(quest_id), count_down(), update_daily_timer()
    print("Sleeping now for 20 seconds.")
    time.sleep(20)




