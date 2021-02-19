import praw
import os

#gives link to a gallery, but not to the individual images

# Create the reddit instance
class reddit_bot:
    def __init__(self):
        self.reddit = praw.Reddit("reddit-bot")
        self.mentions = self.reddit.inbox.mentions
        self.stream = praw.models.util.stream_generator(self.mentions, skip_existing=True)
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
    def parse_flags(self, text):
        flag_messages = ""
        flag_list = ["cmds"] #this will hold all flags that we want to use
        flag_descriptions = [] #this will hold all flag description or names by index for the bot to respond with
        test_list = ["ab","cd","ef","ps","a","cmds"]#list of flags for testing responses
        for flag in test_list:
            if flag in text:
                loc = text.find(flag) #this implementation will only return the index of the first instance of our string
                if loc != 0 and text[loc-1] == '-':
                    flag_messages += "\n\n\nFlag found: -" + flag
        if "cmds" in flag_messages:
            flag_messages +="\n\n\nAll COMMANDS: \n\n\n"
            for flag in test_list:
                flag_messages+="-"+flag+"\n\n\n"
        return flag_messages

    def checkout_mention(self, mention):
        parent_id = mention.parent()
        message = ""
        parent = self.reddit.submission(id=parent_id)
        images = []
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
            message += self.parse_flags(str(mention.body))
            message += "\n\n\n"+self.info
        except Exception as e:
            print(e.__traceback__)
            return "This bot does not reply to image links in comments! Only to initial image posts! :)"+ "\n\n\n"+self.info, parent_id,

        return message, parent_id

    def reply(self,mention, message):
        mention.reply(message)
        '''
        there is a limit to how often you can do this
        comment the mention.reply line when testing, and only want to see prints
        '''

    def run(self):
        print("Bot running...")
        for mention in self.stream:
            msg, parent_id = self.checkout_mention(mention)
            print("***Message:\n", msg,"\nEnd of Message***=============================\n\n")
            if(len(msg) > 0):
                self.reply(mention, msg)

def main():
    bot = reddit_bot()
    bot.run()

if __name__ == "__main__":
    main()

