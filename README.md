# University of Michigan College of Engineering News Center Media Library Audit
(*what a mouthful*)

This program performs a full audit of all *published* items in the Michigan Engineering News Center site's media library. It accomplishes this by leveraging the [WordPress REST API](https://developer.wordpress.org/rest-api/), especially the Media and Users endpoints. The program produces a CSV file that contains the following information about each item in the site's media library:
- Filename (string)
- Dimensions (string)
- File size (string)
- Alt text (string)
- Caption (string)
- Duplicate? (boolean)
- Uploaded by: (string)
- ID (integer)

Since the overwhelming majority of the items in the site's media library are images, many of these criteria are concerned with image qualities (i.e. dimensions, alt text, caption, etc.).

The program can be run by opening the CoE_Media_Audit_program executable file (will need to be unzipped first) and clicking the 'Run' button. The program will take several hours to complete and will place a complete CSV file in your Desktop directory when finished. Please do not close the application window nor the terminal window that appears until the program is finished running. When the program encounters media items which are missing necessary data, it will also place the returned data for these items into a json file titled *news_center_faulty_media.json*. 


## Requirements
The only requirement for running the exectuable file is a mac computer. However, if you would like to modify the source code and/or run the .py file directly from the command line, you will need to have Python and a number of Python modules installed to do so.

### Python
The program is written in Python and therefore requires Python 3 (or higher) to be installed on the computer that it is being run on. Python can be easily downloaded and installed.
[Python Downloads](https://www.python.org/downloads/)

#### Python modules
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [tkinter](https://docs.python.org/3/library/tkinter.html)
- [requests](https://requests.readthedocs.io/en/master/)
- [csv](https://docs.python.org/3/library/csv.html)
- [json](https://docs.python.org/3/library/json.html)


## Planned developments
- Improved UI - tkinter UIs are notoriously ugly; however, the program's current tkinter window could benefit from an improved layout as well as aesthetic modifications.
- Option for user to provide the URL of a different CoE website and have the program perform a media audit of that website.
- Modify the program to simply update a master database of media items, instead of creating a fresh CSV file each time it is run.
- Currently, 'cancelling' or stopping the program while the main loop is running freezes the window for awhile (can last >5 minutes) before the program actually terminates. This needs to be fixed.
