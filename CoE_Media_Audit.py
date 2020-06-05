import requests
import json
import csv
import os
from bs4 import BeautifulSoup
import datetime
import tkinter as tk
from PIL import Image, ImageTk
import tkinter.font as font
import threading
import sys


CURRENT_DATE = datetime.date.today()
CSV_FILENAME = os.path.expanduser("~/Desktop") + (f'/CoE_media_audit_{CURRENT_DATE}.csv')
FAULTY_MEDIA_FILENAME = 'news_center_faulty_media.json'
window = tk.Tk()


#----GLOBAL VARIABLES----#
USER_DATA = {}
USER_DICT = {}
MEDIA_DATA = {}
BASE_URL = None
PROGRESS_BOX = None



#----DATA RETRIEVAL FUNCTIONS----#

def make_media_request():
    ''' Makes a series of GET requests to the Wordpress site's API and builds a list of the returned data.
    Keeps making requests until data stops being returned.

    Parameters
    ------------
    None

    Returns
    --------
    media_data_list : list
        A compiled list of all the returned data from the API requests.
    '''
    
    PROGRESS_BOX.insert(tk.END, 'Retrieving media data...\n')
    media_data_list = []
    i = 1
    user_agent = {'User-agent': 'Mozilla/5.0'}
    global BASE_URL

    while i > 0:
        url = f"{BASE_URL}/wp-json/wp/v2/media?page={i}"
        response = requests.get(url, headers = user_agent)
        media_data = response.json()
        
        if type(media_data) != list: #Successful API requests return data in a list - Failed API requests return data in a series of dictionaries
            i = 0
            break
        else:
            media_data_list.append(media_data)
            i += 1

    return(media_data_list)


def make_user_request():
    ''' Makes a series of GET requests to the Wordpress site API's Users endpoint and builds a list of the returned data.
    Keeps making requests until data stops being returned.

    Parameters
    ------------
    None

    Returns
    --------
    user_data_dict : dict
        A dictionary containing the returned data from the API requests.
    '''

    PROGRESS_BOX.insert(tk.END, 'Retrieving users...\n')
    user_data_dict = {'michigan_engineering_news_center_users' : []}
    i = 1
    user_agent = {'User-agent': 'Mozilla/5.0'}
    global BASE_URL
    
    while i > 0:
        url = f"{BASE_URL}/wp-json/wp/v2/users?page={i}"
        response = requests.get(url, headers = user_agent)
        user_data_raw = response.json()

        for item in user_data_raw: #Stops the loop if a user already exists in the USER_DICT
            if item['id'] in USER_DICT.keys():
                i = 0
                break
        
        if not len(user_data_raw) > 0: #Failed API requests to the 'users' endpoint return empty results, stopping the while loop
            i = 0
            break
        
        else:
            for item in user_data_raw:
                user_data_dict['michigan_engineering_news_center_users'].append(item)
            i += 1

    return(user_data_dict)



#----DATA FORMATTING FUNCTIONS----#

def create_user_dict(user_data_dict):
    ''' Creates a dictionary from the provided user data (json) with the user's id as a key
    and the user's name as a value.

    Parameters
    ------------
    user_data_dict : dict
        a dictionary of items containing data about the users

    Returns
    --------
    None
    '''

    PROGRESS_BOX.insert(tk.END, 'Parsing users...\n')
    for user in user_data_dict['michigan_engineering_news_center_users']:
        user_id = user['id']
        name = user['name']

        USER_DICT[user_id] = name


def get_file_size(media):
    ''' Determines the size of the media file and formats the value (originally in bytes)
    as either MB or KB, depending on size.

    Parameters
    ----------
    media : dict
        a media item retrieved from the source

    Returns
    -------
    file_size : str
        formatted string (either KB or MB, depending on size)
    '''

    user_agent = {'User-agent': 'Mozilla/5.0'}

    response = requests.get(media['guid']['rendered'], headers=user_agent)
    image_source = response.content 
    raw_file_size = len(image_source) #GET requests for images return a "bytes" type object, making it possible to use len() to find the file size (i.e. number of bytes)
    
    if raw_file_size >= 1000000:
        file_size = f"{round(raw_file_size / 1000000, 2)} MB" #2 determines how many digits after the decimal to include (e.g. 4.16)
    else:
        file_size = f"{round(raw_file_size / 1000)} KB"

    return file_size


def process_data(data):
    ''' Processes the data returned from make_media_request() by assiging values
    to the variables necessary for the audit (file_name, dimensions, file_size, alt_text, caption, duplicate, uploader, id).

    Parameters
    ----------
    data : list
        a large list containing all of the media objects retrieved from the source

    Returns
    --------
    media_list : list
        list containing all of the media objects' relevant info for the audit
    '''

    PROGRESS_BOX.insert(tk.END, 'Parsing media data...\n')
    media_list = []
    for media_group in data:
        for media in media_group:
            
            #file name
            try:
                raw_guid = media['guid']['rendered']
                file_name = raw_guid[raw_guid.rfind('/'):][1:] #The returned object is the media url (example:https://cm-web-news-files.s3.amazonaws.com/uploads/2019/12/kovach-FEATURED.png). str.rfind()
            except:                                            #returns the index of the last occurence of the substring '/'. It's an inelegant solution but it was the only reliable method I could come up with to retrieve the filename.
                file_name = 'No filename provided'
                save_cache(media, FAULTY_MEDIA_FILENAME)

            #dimensions
            try:
                dimensions = f"{media['media_details']['sizes']['full']['width']} x {media['media_details']['sizes']['full']['height']}"
            except:
                dimensions = 'No dimensions provided'
                save_cache(media, FAULTY_MEDIA_FILENAME)

            #alt text
            if media['alt_text']:
                alt_text = media['alt_text']
            else:
                alt_text = 'N/A'
            
            #caption
            try:
                caption = str.join("", BeautifulSoup(media['caption']['rendered'], "lxml").text.splitlines()) #splitlines() is used to prevent issues writing strings with multiple lines to a CSV file; .text is used to remove HTML tags
                if not caption:
                    caption = "N/A"
            except:
                caption = "N/A"
                save_cache(media, FAULTY_MEDIA_FILENAME)
            
            #author
            try:
                uploader = USER_DICT[media['author']]
            except:
                uploader = 'Could not retrieve author'
                save_cache(media, FAULTY_MEDIA_FILENAME)

            #duplicate
            duplicate = False
            for item in media_list:
                if item[0] == file_name:
                    duplicate = True
                    item[5] = True

            #file size
            try:
                file_size = get_file_size(media)
            except:
                file_size = 'Could not retrieve file size'
                save_cache(media, FAULTY_MEDIA_FILENAME)

            #ID
            try:
                media_id = media['id']
            except:
                media_id = 'Could not locate ID'
                save_cache(media, FAULTY_MEDIA_FILENAME)

            media_item = [file_name, dimensions, file_size, alt_text, caption, duplicate, uploader, media_id] 
            media_list.append(media_item)
            
    return(media_list)


def write_csv_file(media_list):
    ''' Writes contents to a csv file

    Parameters
    ------------
    media_list : list
        nested list of a media items' data

    Returns
    --------
    None
    '''

    PROGRESS_BOX.insert(tk.END, 'Writing data to CSV file...\n')
    with open(CSV_FILENAME, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        header_row = ['Filename', 'Dimensions', 'File size', 'Alt Text', 'Caption', 'Duplicate?', 'Uploaded by', 'ID']
        csv_writer.writerow(header_row)

        
        for item in media_list:
            media_row = [item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]]
            csv_writer.writerow(media_row)



#----CACHING FUNCTIONS----#

def save_cache(cache_dict, cache_filename):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''

    dumped_json_cache = json.dumps(cache_dict)
    fw = open(cache_filename,"a")
    fw.write(dumped_json_cache)
    fw.close()


def open_cache(filename):
    ''' Opens the cache file if it exists and loads the JSON data
    
    Parameters
    ----------
    None
    
    Returns
    -------
    cache_dict : dict
        the opened cache
    '''

    try:
        cache_file = open(filename, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    
    return cache_dict



#----MISC FUNCTIONS----#

def resource_path(relative_path):
    ''' Creates an absolute path for objects based on the user's directories.

    Parameters
    ----------
    relative path: str
        essentially just the item's filename

    Returns
    -------
    the formatted absolute path for the file: str
    '''

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



#----USER INPUT VALIDATION FUNCTIONS----#

def validate_url(url):
    '''Uses the requests module to verify that the url entered by the user is valid.
    If the url is invalid, inserts an error message into the GUU

    Parameters
    ----------
    url : str
        the url entered by the user

    Returns
    -------
    True/False : Boolean
    '''

    global PROGRESS_BOX
    user_agent = {'User-agent': 'Mozilla/5.0'}
    
    try:
        requests.get(url, headers = user_agent)
        return True
    except:
        PROGRESS_BOX.insert(tk.END, 'ERROR - INVALID URL\n')
        return False


def process_url(url):
    '''Uses the validate_url() helper function to verify that the url exists.
    If it does, then the url string is formatted to make sure it can function properly
    as a base url for the API call

    Parameters
    ----------
    url : str
        the url entered by the user

    Returns
    -------
    formatted_url : str
        the cleaned up string that will function as the base url for the API call
    '''

    if validate_url(url) is True:
        if url[-1] == '/':
            formatted_url = url[:-1]
        else:
            formatted_url = url
    else:
        formatted_url = None

    return formatted_url



#----GUI FUNCTIONS----#

def display_gui():
    ''' Creates the tkinter window and populates it with labels, buttons, and a text box.

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''
    
    #window title
    window.title("Michigan Engineering Media Audit")

    #window size
    window.geometry("575x575")

    #title font setting
    title_font = font.Font(size=30)

    #logo image
    image = Image.open(resource_path("michigan_logo.jpg"))
    photo = ImageTk.PhotoImage(image)

    #labels
    logo = tk.Label(master=window, image=photo, pady=10, padx=10)
    logo.grid(column=0, row=0)

    title = tk.Label(master=window, text="Michigan Engineering\nMedia Audit", font=title_font, justify='left')
    title.grid(column=1, row=0, sticky='w')

    program_description1 = tk.Label(master=window, padx=10, text="This program performs a full audit of a Michigan Engineering WordPress website's media\nlibrary by retrieving data about each item in the library and formatting that\ndata in a CSV file.\n\nRetrieving the necessary data requires making over 1,000 calls to the website's API.\nTherefore, it is important that you only run this program when others are not likely\nto be using the website (ideally after 6pm EST), as too much traffic can negatively\nimpact the site's performance.\n\nOnce you run the program, it will take several hours to complete the audit.\nPlease do not close this window while the program is running\n\nEnter the website's base url (e.g. https://news.engin.umich.edu)", justify='left')
    program_description1.grid(columnspan=4, row=1)

    #entries
    url_entry = tk.Entry(width=45)
    url_entry.grid(column=0, row=2, padx=10, columnspan=2, sticky='w')


    #This implementation could be vastly improved. This is just the only way I could get it to work for now (first time implementing threading).
    def handle_click():
        ''' Handles the user's click by implementing multithreading for the main function - main_func() - in order to enable main_func()
        to update the PROGRESS_BOX Text widget while also preventing the tk window from freezing.

        Parameters
        ----------
        None

        Returns
        -------
        None
        '''

        global BASE_URL
        BASE_URL = str(url_entry.get())

        def main_func():
            ''' The main function of the program. Calls several other functions to retrieve data, format it, and produce a CSV file.

            Parameters
            ----------
            None

            Returns
            --------
            None
            '''
            
            global MEDIA_DATA
            global BASE_URL
            global PROGRESS_BOX

            #progress text box
            PROGRESS_BOX = tk.Text(master=window, height=10, width=75)
            PROGRESS_BOX.grid(columnspan=4, row=3, padx=10)

            PROGRESS_BOX.insert(tk.END, 'Running...\n')

            if BASE_URL != None:
                    PROGRESS_BOX.insert(tk.END, f'Connecting to {BASE_URL}\n')
                    BASE_URL = process_url(BASE_URL)
                    if  BASE_URL == None: #if process_url is unable to verify that the url is valid, then it will return None
                        return # empty returns are used to stop function from continuing if an error is encountered

            try:
                create_user_dict(make_user_request())
            except:
                PROGRESS_BOX.insert(tk.END, 'ERROR - COULD NOT RETRIEVE USERS\n')
                return

            try:
                MEDIA_DATA = make_media_request()
            except:
                PROGRESS_BOX.insert(tk.END, 'ERROR - COULD NOT RETRIEVE MEDIA DATA\n')
                return

            try:
                write_csv_file(process_data(MEDIA_DATA))
            except:
                PROGRESS_BOX.insert(tk.END, 'ERROR - COULD NOT PARSE MEDIA DATA.\n')
                return

            PROGRESS_BOX.insert(tk.END, f'Finished! You can find the complete CSV file at {CSV_FILENAME}')
        
        t = threading.Thread(target= main_func)
        t.start()

    #buttons
    run_button = tk.Button(master=window, text="Run", pady=15, width=15, command= handle_click)
    run_button.grid(column=0, columnspan=1, row=4, padx=10, pady=10, sticky='w')

    cancel_button = tk.Button(master=window, text="Cancel", command=sys.exit, pady=15, width=15)
    cancel_button.grid(column=1, row=4, pady=10, sticky='w')

    window.mainloop()


if __name__ == "__main__":
    display_gui()