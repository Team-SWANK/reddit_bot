import logging, os, io, base64, requests
import praw
import pyimgur
import numpy as np
import urllib.request
from PIL import Image
from imgur_auth import get_client_id
from dotenv import load_dotenv

load_dotenv( dotenv_path='/.env', encoding='utf-8' )

segment_url = os.getenv("SEGMENT_URL")
censor_url = os.getenv("CENSOR_URL")

# Create the reddit instance
class reddit_bot:
    def __init__(self):
        self.reddit = praw.Reddit("reddit-bot")
        self.comments = self.reddit.inbox.unread(limit=None)
        self.info = "\n\n\nPhotoSense is a set of online tools that give people the ability to protect their privacy. " \
                    "The Reddit social media bot can be utilized by anyone who wants to spread this movement " \
                    "by using the appropriate hashtags (u/PhotoSenseBot) and flag commands. Enter ' -cmds ' while mentioning " \
                    "this bot to retrieve a list of flag commands."
        self.invoking_commands_message = "\n\nEnsure that a dash is placed before listing the commands. Invoke the bot using "\
                    "u/PhotoSenseBot -cmds for a list of commands, including examples of how a bot can be invoked."

    #As of right now this only serves to return the image_urls and flags for the webapp to process
    def send_to_webapp(self, image_urls, flags):
        return image_urls, flags

    #As of right now, this only serves to return an app_url from the webapp for a session with the image
    def send_from_webapp(self, app_url):
        return app_url

    #Parses the body of the comment for any flags
    def parse_flags(self, text):
        flags_found = []
        flag_messages = ""

        flags = {
            'cmds': 'view bot commands',
            'rmv': 'remove parent comment with censored image',
            'px': 'apply pixelsorting algorithm to image',
            'sb': 'apply simple blurring algorithm to image', 
            'pz': 'apply pixelization algorithm to image',
            'bb': 'apply black bar censoring to image',
            'fi': 'apply fill in censoring to image',
        } 
        flag_descriptions = flags.values() 

        if "cmds" in text:
            flags_found.append('cmds')
            flag_messages += "\n\n All Image Censoring Commands \n\n"
            
            for flag in flags.keys():
                description = flags.get(flag)
                flag_messages += "(-" + flag +")" + " " + description + "\n\n"

            flag_messages += "The following example invokes the bot to return a censored image using " \
                "the pixel sorted algorithm: u/PhotoSenseBot -px" + "\n\n"
            flag_messages += "Multiple censoring algorithms can be used as long as they are inserted after the dash. " \
                "The following example invokes the bot to return a censored image using multiple commands: u/PhotoSenseBot -px sb px"
        elif '-' in text:
            # gets command without 'u/PhotoSenseBot'
            command =  text.split('u/PhotoSenseBot \\')[1] 
            dash_index = 0

            # ensure commands are listed after the dash mark
            if '-' in command[dash_index]:
                # skip the 'cmds' command and start with the second key in flags instead
                start_index = 1 
                # append all flags that exist in the command 
                for flag in flags.keys()[start_index:]:
                    if flag in command:
                        description = flags.get(flag)
                        flag_messages += "\n\nFlag found: (-" + flag + ") " + description
                        flags_found.append(flag)
            else: 
                flag_messages += self.invoking_commands_message
        else: 
            print('No flags were found')
            flag_messages += self.invoking_commands_message
        
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
        flag_msg, flags = self.parse_flags(str(mention.body))

        if "rmv" in flags:
            print("comment ID: ", mention.id)
            self.delete_post(mention)
            return "", mention.id
        try:
            keys = ['.jpg', '.jpeg', '.png', '.jfif', 'gallery']
            if any (key in parent.url for key in keys):
                print('parent url: ' + parent.url)
                # if user enters multiple images
                if('gallery' in parent.url): 
                    print('found gallery instance')
                    gallery_data = parent.media_metadata
                    message, images = self.get_images_from_gallery(gallery_data)
                # if user enters a single image
                else: 
                    images.append(parent.url)
                    message += "\nImage found! \nImage URL(s): " + str(images)  # a double \n, marks for a newline in reddit

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
                    print('***end of selftext***')

                    if('gallery' in parent.selftext): 
                        print('detected gallery')
                    else:
                        for i in range(num_images):
                            unstripped_URL = selftext.split("https://")[i+1]  # for each link, take the split section with the actual part of the link (caption removed)
                            print('unstripped url: ' + unstripped_URL)
                            image_URL = unstripped_URL.split(')')[0]  # strip the closing' ) ' and the rest of remaining selftext
                            print('image url: ' + image_URL)
                            if '.jpg' or '.jpeg' or '.png' or ".jfif" in image_URL:  # use this to confirm it's a link to an image, and not to another site 
                                images.append("https://"+image_URL)  # add it to our list of links to print

                    message += "\n\nImage(s) found! \n\nImage URL(s): " + str(images)  # a double \n, marks for a newline in reddit
            else:
                message += "\n\nNo Image found in post!"
            message += flag_msg
            message += "\n\n"+self.info
        except Exception as e:
            print(e.__traceback__)
            return "This bot does not reply to image links in comments! Only to initial image posts! :)"+ "\n\n\n"+self.info, parent_id,

        return message,parent_id,images

    def get_images_from_gallery(self, data):
        images = [] 
        msg = ''
        if(len(data) > 0): 
            for media_id in data:
                image_data = data[media_id]
                if image_data['e'] == 'Image':
                    image_url = image_data['p'][-1]['u'] # Get most high quality image url (last one that appears in the link list)
                    images.append(image_url)

            msg += "\nImage found! \nImage URL(s): " + str(images)  # a double \n, marks for a newline in reddit
        else:
            msg += "\nNo image was found\n"
        
        return msg, images

    #Sends a reply through reddit
    def reply(self, mention, message, images):
        imgur_links = []
        if(len(images) > 0):
            i = 0 
            file_names = []
            for image in images: 
                print('image: ' + image) 
                temp_image = 'temp' + str(i) + '.jpg'
                temp_mask_image = 'mask' + str(i) + '.jpg'
                temp_censored_image = 'censored' + str(i) + '.jpg'

                # Call Segmentation API for each image
                with urllib.request.urlopen(images[i]) as url:
                    with open(temp_image, 'wb') as f: 
                        f.write(url.read())
                files = {'image': open(temp_image, 'rb')}
                res = requests.post(segment_url, files=files).json()
                print('completed segmentation request')

                # Convert each segmentation to image file and call censoring api
                mask_to_image(res["predictions"]).save(temp_mask_image)
                files = {'image': open(temp_image, 'rb'), 'mask': open(temp_mask_image, 'rb')}
                res = requests.post(censor_url, files=files)
                print('completed censoring request')

                # Convert base64 response to image file 
                if res.status_code == 200: 
                    fn = temp_censored_image
                    img_bytes = res.json()['ImageBytes'].encode()
                    with open(fn, 'wb') as f: 
                        f.write(base64.decodebytes(img_bytes))
                    i += 1
                    file_names.append(fn)
                else:
                    print('response status was not equal to 200')
                

            print('files names: \n')
            print(file_names)

            if(len(file_names) > 0): 
                print('hello')
                # Upload image to imgur
                imgur_links = upload_to_imgur(file_names)
                print('imgur links: ')
                print(imgur_links)
                message += '\n\n Imgur Links: ' + str(imgur_links)
                # mention.reply(imgur_link)
                # self.remove_local_image()
            else:
                print('\n\nError in processing requests')
                message += '\n\nError in processing requests'
                mention.reply(message) 
                
            '''
            there is a limit to how often you can do this
            comment the mention.reply line when testing, and only want to see prints
            '''
        else:
            print('No images were found')
            # mention.reply(message)    

    def remove_local_image(self): 
        os.remove('local-image.jpg')
        if os.path.exists('local-image.jpg') is False: 
            print('image removed locally')
        else: 
            print('file still exists')

    #deletes a post if
    def delete_post(self,mention):
        print("===Deleting response===")
        sub = mention.submission #returns the submission object
        sub_auth = sub.author #submission author
        comm_to_del = mention.parent() #delete the parent of the mentioner
        init_mentioner = comm_to_del.parent() #will be used to check if the mentioner wants to delete their own bot response
        if((mention.author == sub_auth) or (mention.author == init_mentioner)) and (comm_to_del.author == "PhotoSenseBot"):
            comm_to_del.delete() # will be comm_to_del.delete()
            print("Successfully removed!")
        else: print("Unsuccessful removal!")
        return

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
        found_images = []
        print("Bot running...")
        self.mark_r() #prevents responding to comments that were made while bot was asleep

        while(True):
            self.comments = self.reddit.inbox.unread(limit=None)
            #must reinstantiate the unread stream or else it won't enter loop below

            for comment in self.comments:
                if comment and isinstance(comment,praw.models.reddit.comment.Comment) and ("u/PhotoSenseBot" in comment.body) :
                    msg,_,found_images = self.checkout_mention(comment)
                    print("***Message:\n", msg, "\nEnd of Message***=============================\n\n")
                    if (len(msg) > 0):
                        self.reply(comment, msg, found_images)
                    self.reddit.inbox.mark_read([comment])
                break

def upload_to_imgur(images):
    if(len(images) > 0): 
        print('uploading images to imgur: \n')
        print(images)

        imgur_links = []
        i =  0
        client_id = get_client_id()

        for image in images:  
            path = images[i]
            im = pyimgur.Imgur(client_id)
            uploaded_image = im.upload_image(path, title="Uploaded with PyImgur")
            imgur_links.append(uploaded_image.link)
            i += 1

        return imgur_links
    else:
        return []

def mask_to_image(pixels): 
    arr = np.zeros([len(pixels), len(pixels[0]), 3], dtype=np.uint8)
    for i in range(len(pixels)): 
        for j in range(len(pixels[0])): 
            if pixels[i][j] == 0: 
                arr[i, j] = [0, 0, 0]
            else: 
                arr[i, j] = [255, 255, 255]
    return Image.fromarray(arr)

def main():
    bot = reddit_bot()
    bot.run()

if __name__ == "__main__":
    main()

