import logging, os, io, base64, requests, sys
import praw
import pyimgur
import numpy as np
import urllib.request
from PIL import Image
sys.path.insert(1, '/imgur')
from imgur.imgur_auth import get_client_id
from dotenv import load_dotenv, find_dotenv

load_dotenv(dotenv_path=find_dotenv())

segment_url = os.getenv("SEGMENT_URL")
censor_url = os.getenv("CENSOR_URL")
web_app_url = os.getenv("WEB_APP_URL")

# Create the reddit instance
class reddit_bot:
    def __init__(self):
        self.reddit = praw.Reddit("reddit-bot")
        self.comments = self.reddit.inbox.unread(limit=None)
        self.info = "\n\n\nPhotoSense is a set of online tools that give people the ability to protect their privacy. " \
                    "The Reddit social media bot can be utilized by anyone who wants to spread this movement " \
                    "by using the appropriate hashtags (u/PhotoSenseBot) and flag commands. Enter 'u/PhotoSenseBot cmds' " \
                    "to retrieve a list of flag commands."

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
            'px': 'apply the pixel sorting algorithm',
            'sb': 'apply the simple blurring algorithm (gaussian blur)', 
            'pz': 'apply the pixelization algorithm',
            'bb': 'apply the black bar censoring algorithm',
            'fi': 'apply the fill in censoring algorithm',
        } 
        
        if "cmds" in text:
            flag_descriptions = flags.values() 
            flags_found.append('cmds')

            # instantiate a message response for displaying all commands
            flag_messages += "\n\nAll Image Censoring Commands\n\n"
            for flag in flags.keys():
                description = flags.get(flag)
                flag_messages += "(" + flag +")" + " " + description + "\n"

            flag_messages += "\nThe following example invokes the bot to return a censored image using " \
                "the pixel sorting algorithm: u/PhotoSenseBot px \n" 
            flag_messages += "Multiple censoring algorithms can be used as well. " \
                "The following example invokes the bot to return a censored image using multiple commands: u/PhotoSenseBot px sb pz"     
        else:
            arr = text.split()
            if('u/PhotoSenseBot' in arr): 
                arr.remove('u/PhotoSenseBot')

            for i in range(len(arr)): 
                arr[i] = arr[i].lower()

            if 'px' in arr:
                flags_found.append("pixel_sort")
            if 'pz' in arr:
                flags_found.append("pixelization")
            if 'sb' in arr:
                flags_found.append("gaussian_blur")
            if 'bb' in arr:
                flags_found.append("black_bar")
            if 'fi' in arr:
                flags_found.append("fill_in")
            if 'rmv' in arr:
                flags_found.append("remove")
            
            if(len(flags_found) == 0): 
                flag_messages += "\n" + self.info
        
        return flag_messages, flags_found

    '''
    Checks the mention and parses through to find the image in the parent post. All image url's are extracted, and 
    the body is parsed for flags. Also does the main assessment for what the reply text will be.
    '''
    def checkout_mention(self, mention):
        parent_id = mention.parent()
        parent = self.reddit.submission(id=parent_id)
        message = ""
        images = []
 
        try:
            keys = ['.jpg', '.jpeg', '.png', '.jfif', 'gallery']
            text_only_post = parent.is_self
            # determine the reddit post type: text, image/video, url
            if text_only_post:
                selftext = parent.selftext
                # check if an image was posted in the text
                if any (key in selftext for key in keys):
                    num_images = parent.selftext.count("https://") # check how many links we have total in the text 
                    
                    for i in range(num_images):
                        unstripped_URL = selftext.split("https://")[i+1]  # for each link, take the split section with the actual part of the link (caption removed)
                        image_URL = unstripped_URL.split(')')[0]  # strip the closing' ) ' and the rest of remaining selftext
                        if '.jpg' or '.jpeg' or '.png' or ".jfif" in image_URL:  # use this to confirm it's a link to an image, and not to another site 
                            images.append("https://"+image_URL)  # add it to our list of links to print
            else: 
                # check if an image was posted in the url 
                if any (key in parent.url for key in keys):
                    # if user enters multiple images aka 'gallery' in reddit
                    if('gallery' in parent.url): 
                        gallery_data = parent.media_metadata
                        images = self.get_images_from_gallery(gallery_data)
                    # if user enters a single image
                    else: 
                        images.append(parent.url)
            
        except Exception as e:
            # print('throwing exception')

            # print(e.__traceback__)
            self.delete_post(mention)
            return "", mention.id, [], []
            # return "This bot does not reply links in comments! Only to initial image posts! :)"+ "\n\n\n"+self.info, parent_id,

        if(len(images) == 0): 
            print("no image was found") 
            message += "\n\nNo image was found\n\n"
            mention.reply(message)
            return "", mention.id, [], []

        else: 
            comment_body = str(mention.body)
            flag_msg, flags = self.parse_flags(comment_body)

            if "remove" in flags:
                print("Deleting post: ", mention.id)
                # self.delete_post(mention)
                return "", mention.id, [], flags
            else:
                message += flag_msg 
                return message, parent_id, images, flags


    def get_images_from_gallery(self, data):
        images = [] 
        if(len(data) > 0): 
            for media_id in data:
                image_data = data[media_id]
                if image_data['e'] == 'Image':
                    image_url = image_data['p'][-1]['u'] # Get most high quality image url (last one that appears in the link list)
                    images.append(image_url)
        
        return images

    # Sends a reply through reddit
    def reply(self, mention, message, images, flags):
        # respond with all commands
        if('cmds' in flags or len(flags) == 0):
            print(message)
            mention.reply(message)   
        else:  
            imgur_links = []
            file_names = []
            temp_images = [] 

            temp_censor_url = censor_url
            total_flags = len(flags)
            # instantiate temp censor url according to flags set by user 
            for i in range(total_flags):
                if(i == total_flags - 1): 
                    temp_censor_url += flags[i] + "]"
                else: 
                    temp_censor_url += flags[i] + ", "

            for i in range(len(images)): 
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
                # add a temp image to be used later in case user wants to edit segmentations via web app
                temp_images.append(temp_image)

                # Convert each segmentation to an image file 
                mask_to_image(res["predictions"]).save(temp_mask_image)
                files = {'image': open(temp_image, 'rb'), 'mask': open(temp_mask_image, 'rb')}

                # Call the censorship api
                res = requests.post(temp_censor_url, files=files)
                print('completed censoring request')

                # Convert base64 response file 
                if res.status_code == 200: 
                    fn = temp_censored_image
                    img_bytes = res.json()['ImageBytes'].encode()
                    with open(fn, 'wb') as f: 
                        f.write(base64.decodebytes(img_bytes))
                    i += 1
                    file_names.append(fn)
                else:
                    print('response status was not equal to 200')

            if(len(file_names) > 0): 
                # Upload image to imgur
                imgur_links = upload_to_imgur(file_names)
                original_image_links = upload_to_imgur(temp_images)
                
                re_edit_images_links = []
                for original_image in original_image_links: 
                    re_edit_images_links.append(web_app_url + original_image)

                message += '\n\nHere are your censored images\n\n'
                message += str(imgur_links) + '\n'
                message += '\nIf you are dissatisfied with an image segmentation(s), copy and paste one of the links'
                message += '\nbelow in your browser to edit an image segmentation using the PhotoSense web app\n\n'
                message += str(re_edit_images_links) + '\n'  
                print(message)
                mention.reply(message)
                # self.remove_local_image()
            else:
                print('\n\nError in processing requests')
                message += '\n\nError in processing requests'
                mention.reply(message) 
                    
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
        else: 
            print("Unsuccessful removal!")
        

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
        found_images = []
        flags = []
        
        self.mark_r() #prevents responding to comments that were made while bot was asleep

        while(True):
            self.comments = self.reddit.inbox.unread(limit=None)
            #must reinstantiate the unread stream or else it won't enter loop below
            for comment in self.comments:
                if comment and isinstance(comment,praw.models.reddit.comment.Comment) and ("u/PhotoSenseBot" in comment.body):
                    msg,_,found_images,flags = self.checkout_mention(comment) 
                    if(len(found_images) > 0): 
                        self.reply(comment, msg, found_images, flags)
                    self.reddit.inbox.mark_read([comment])
                break

def upload_to_imgur(images): 
    print('uploading images to imgur: \n')
    print(images)

    imgur_links = []
    client_id = os.getenv('IMGUR_CLIENT_ID')
    i = 0

    for image in images:  
        path = images[i]
        im = pyimgur.Imgur(client_id)
        uploaded_image = im.upload_image(path, title="Uploaded with PyImgur")
        imgur_links.append(uploaded_image.link)
        i += 1

    return imgur_links

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

