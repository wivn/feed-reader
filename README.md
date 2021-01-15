# Your Wonderful Feed Reader
## Purpose of the Project

I wanted an RSS feed reader that could match the exact feature-set I was looking for. I was also looking to play around with test-driven development and fully-tested software. This project includes a comprehensive test suite including both unit tests and integration tests. 

## Features
- Subscribe to any [RSS](https://en.wikipedia.org/wiki/RSS) feed or [h_feed](http://microformats.org/wiki/h-feed)
- Login via regular username+password or with [IndieAuth](https://www.w3.org/TR/indieauth/)
- Filter for to get only the latest stories
- You can read the articles you've added within the web app (depending on what the RSS feed provides)
- Add pages from feeds (or any page in general) to your "Current" page
	- Something I've always wanted to do is to be able to get all the main links on a page and save them for reading later. You can do this on the "Current" page

## How

This project was built using Python and Django. Various other libraries were used to provide additional functionality (eg. feedparser, Selenium, BeautifulSoup4, bleach, mf2py, etc). See requirements.txt to find all the dependencies.

## Running the project
This project requires Python version 3.7.5 or later.
- Run `pip install -r requirements.txt` to install all the dependencies.
- Run `python manage.py runserver`. This will start a local server running on your localhost:3000 port
- Run `python manage.py test` to run the test suite. Currently, the test suite requires the use of Safari. You'll also need to ensure that you've enabled "Allow Remote Automation" in the Safari Develop settings.