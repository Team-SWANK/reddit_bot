import praw
import os
import time
#gives link to a gallery, but not to the individual images

# Create the reddit instance
class reddit_bot:
    def __init__(self):
        self.reddit = praw.Reddit("reddit-bot")
        self.mentions = self.reddit.inbox.mentions
        #self.comments = self.reddit.inbox.comment_replies()
        self.comments = self.reddit.inbox.unread(limit=None)
        self.stream_c = praw.models.util.stream_generator(self.comments, skip_existing=True, pause_after = 1)
        self.stream = praw.models.util.stream_generator(self.mentions, skip_existing=True, pause_after = 1)
        self.info = "\n\n\nPhotoSense is a set of online tools that give people the ability to protect their privacy. " \
                    "In modern movements, many activists and journalists are using the internet to upload images of protests and " \
                    "other politically charged mass gatherings. However, those who upload their images online may be " \
                    "susceptible to threats, job loss, and physical assault. PhotoSense addresses " \
                    "this issue by providing twitter and reddit bots, a browser extension, and a web application for users" \
                    " to edit and upload censored images online. PhotoSense is not only an application, it is a movement." \
                    " We strive to emphasize the invaluable rights to peacefully gather, while maintaining the security " \
                    "of privacy. In order to further this movement, PhotoSense provides its users with a Google Chrome " \
                    "Extension, as well as Reddit and Twitter bots. The Google Chrome Extension can be accessed by " \
                    "clicking the link in the top navigation bar of our web application. " \
                    "The Reddit social media bot can be utilized by anyone who wants to spread this movement " \
                    "by using the appropriate hashtags (u/PhotoSenseBot) and flag commands. Enter ' -cmds ' while mentioning " \
                    "this bot to retrieve a list of flag commands."

    #As of right now this only serves to return the image_urls and flags for the webapp to process
    def send_to_webapp(self, image_urls, flags):
        return image_urls, flags

    #As of right now, this only serves to return an app_url from the webapp for a session with the image
    def send_from_webapp(self, app_url):
        return app_url

    #Parses the body of the comment for any flags
    def parse_flags(self, text):
        flag_messages = ""

        #should probably change this to a dictionary key = flag, value = description
        flag_list = ["cmds","rmv"] #this will hold all flags that we want to use
        flag_descriptions = [] #this will hold all flag description or names by index for the bot to respond with
        test_list = ["ab","cd","ef","ps","a","cmds", "rmv"]#list of flags for testing responses
        flags_found = []
        for flag in test_list:
            if flag in text:
                loc = text.find(flag) #this implementation will only return the index of the first instance of our string
                if loc != 0 and text[loc-1] == '-':
                    flag_messages += "\n\n\nFlag found: -" + flag
                    flags_found.append(flag)
        if "cmds" in flag_messages:
            flag_messages +="\n\n\nAll COMMANDS: \n\n\n"
            for flag in test_list:
                flag_messages+="-"+flag+"\n\n\n"
        return flag_messages,flags_found

    '''
    Checks the mention and parses through to find the image in the parent post. All image url's are extracted, and 
    the body is parsed for flags. Also does the main assessment for what the reply text will be.
    '''
    def checkout_mention(self, mention):
        print("=======MENTION FOUND======")
        parent_id = mention.parent()
        message = ""
        parent = self.reddit.submission(id=parent_id)
        images = []
        flag_msg,flags = self.parse_flags(str(mention.body))
        if "rmv" in flags:
            print("comment ID: ", mention.id)
            self.delete_post(mention)
            return "", mention.id
        try:
            keys = ['.jpg', '.jpeg', '.png', '.jfif', 'gallery']
            if any (key in parent.url for key in keys):
                images.append(parent.url)
                message += "\n\nImage found! \n\nImage URL(s): " + str(images)  # a double \n, marks for a newline in reddit

            elif any (key in parent.selftext for key in keys):
                    '''
                    Had to account for the case where for some reason the keys would be foud in the selftext, but the
                    selftext was actually empty. Also had to work around whether or not somebody adds text to the original post.
                    Also had to work around when someone puts a caption to the image, there is an extra ')' at the end.
                    This might break if somebody posts other links in a post with an image in it.
                    '''
                    images = [] #reset images
                    num_images = parent.selftext.count("https://")  # check how many links we have total in the text
                    selftext = parent.selftext
                    print("selftext: ",selftext,"\n***")

                    for i in range(num_images):
                        unstripped_URL = selftext.split("https://")[i+1]  # for each link, take the split section with the actual part of the link (caption removed)
                        image_URL = unstripped_URL.split(')')[0]  # strip the closing' ) ' and the rest of remaining selftext
                        if '.jpg' or '.jpeg' or '.png' or ".jfif" in image_URL:  # use this to confirm it's a link to an image, and not to another site
                            images.append(image_URL)  # add it to our list of links to print

                    print(type(mention))
                    message += "\n\nImage(s) found! \n\nImage URL(s): " + str(images)  # a double \n, marks for a newline in reddit
            else:
                message += "\n\nNo Image found in post!"
            message += flag_msg
            message += "\n\n\n"+self.info
        except Exception as e:
            print(e.__traceback__)
            return "This bot does not reply to image links in comments! Only to initial image posts! :)"+ "\n\n\n"+self.info, parent_id,

        return message,parent_id

    #Sends a reply through reddit
    def reply(self,mention, message):
        mention.reply(message)
        '''
        there is a limit to how often you can do this
        comment the mention.reply line when testing, and only want to see prints
        '''
    def delete_post(self,mention):
        print("===Deleting response===")
        sub = mention.submission #returns the submission object
        sub_auth = sub.author #submission author
        comm_to_del = mention.parent() #delete the parent of the mentioner
        init_mentioner = comm_to_del.parent() #will be used to check if the mentioner wants to delete their own bot response
        if((mention.author == sub_auth) or (mention.author == init_mentioner)) and (comm_to_del.author == "PhotoSenseBot"):
            comm_to_del.delete() # will be comm_to_del.delete()
            print("Successfully removed!")

    #deletes all unread comments waiting in the unread stream
    def mark_r(self):
        #create new stream object so it doesn't interfere with the class one
        comms = self.reddit.inbox.unread(limit=None)
        read_comments = []
        for comment in comms:
            if comment and isinstance(comment, praw.models.reddit.comment.Comment):
                read_comments.append(comment)
        if(len(read_comments)>0):
            self.reddit.inbox.mark_read(read_comments)
            print("Marked comments read: ", read_comments)

    def run(self):
        print("Bot running...")
        self.mark_r()

        id = None #used to compare if the mention is the same as the comment
        while(True):

            for mention in self.stream:
                print("M")
                if mention:
                    print(type(mention))
                    print("Mention")
                    msg,pid = self.checkout_mention(mention)
                    print("***Message:\n", msg,"\nEnd of Message***=============================\n\n")
                    if(len(msg) > 0):
                         self.reply(mention, msg)
                         id = mention.id
                break

            self.comments = self.reddit.inbox.unread(limit=None)
            #must reinstantiate the unread stream or else it won't enter loop below

            for comment in self.comments:
                print("C")
                if id == comment.id:
                    self.reddit.inbox.mark_read([comment])
                    break

                if comment and (id != comment.id) and isinstance(comment,praw.models.reddit.comment.Comment) and ("u/PhotoSenseBot" in comment.body) :
                    print("Comment: ",comment.id,"===", id)
                    msg,pid = self.checkout_mention(comment)
                    print("***Message:\n", msg, "\nEnd of Message***=============================\n\n")
                    if (len(msg) > 0):
                        self.reply(comment, msg)
                    self.reddit.inbox.mark_read([comment])
                break


    def run2(self):
        print("Bot running...")
        while(True):
            print("While")
            end_timer = time.time()+1
            if praw.models.reddit.comment.Comment in self.stream:
                print("M")
                for mention in self.stream:
                    print(type(mention))
                    print("Mention")
                    msg = self.checkout_mention(mention)
                    print("***Message:\n", msg,"\nEnd of Message***=============================\n\n")
                    if(len(msg) > 0):
                        self.reply(mention, msg)
                    if(time.time() > end_timer):
                        break
            elif praw.models.reddit.comment.Comment in self.stream_c:
                print("C")
                for comment in self.comments:
                    print("Comment")
                    end_timer = time.time() + 1
                    msg = self.checkout_mention(comment)
                    print("***Message:\n", msg, "\nEnd of Message***=============================\n\n")
                    if (len(msg) > 0):
                        self.reply(comment, msg)
                    if (time.time() > end_timer):
                        break

        print("here")

def main():
    bot = reddit_bot()
    bot.run()

if __name__ == "__main__":
    main()

