#Brandon Lo
#CS496 OAuth 2.0 Assignment 3
#2/11/18

#import modules taken from the lecture video
#implementing template with webapp2, used for the oauth page
#https://webapp2.readthedocs.io/en/latest/tutorials/gettingstarted/templates.html
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
#using urlfetch to get HTTP requests
#https://cloud.google.com/appengine/docs/standard/python/issue-requests
from google.appengine.api import urlfetch
import webapp2
import urllib
import json
import datetime
import logging
#string and random is used to generate the authorization code
import random
import string

#for debugging
import sys
'''
general format of of a handle user sign in
https://accounts.google.com/o/oauth2/v2/auth?
response_type=code&&
client_id=148747034086-73gqckaik7f0ta5dqea8hfo2ovsj22u5.apps.googleusercontent.com&
redirect_uri=https://oauth-194607.appspot.com/oauth&scope=email&state=0PF4XcD4jsAKZHFQO1Sf8XPQ
'''

#main page that shows the my name the requirements
class MainPage(webapp2.RequestHandler):
    def get(self):
        #logging.debug("The contents of the GET request are:" + repr(self.request.GET))
        #Create a random string for the authorization code
        #https://developers.google.com/actions/identity/oauth2-code-flow
        #How to create a random string with length of 32 needed for the auth code
        #https://stackoverflow.com/questions/37675280/how-to-generate-a-random-string
        #overall the accumulator makes a long url string to send a request
        randomString = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
        url = "https://accounts.google.com/o/oauth2/v2/auth?"
        url = url + "scope=email"
        url = url + "&access_type=offline"
        url = url + "&include_granted_scopes=true"
        url = url + "&state=" + randomString
        url = url + "&redirect_uri=https://oauth-194607.appspot.com/oauth"
        url = url + "&response_type=code"
        url = url + "&client_id=148747034086-73gqckaik7f0ta5dqea8hfo2ovsj22u5.apps.googleusercontent.com"
        getAuthorization = {'url': url}
        self.response.out.write(template.render('index.html', getAuthorization))

#oAuth to get the google+ information
class OauthHandler(webapp2.RequestHandler):
    def get(self):
        #self.response.write("hello")
        #variables used to check if the content requested is avaliable
        checkName = False
        checkProfile = False
        code = self.request.GET['code']
        state = self.request.GET['state']
        #How to handle the post code
        #https://developers.google.com/identity/protocols/OAuth2InstalledApp
        postBody = {
            'code': code,
            'client_id': "148747034086-73gqckaik7f0ta5dqea8hfo2ovsj22u5.apps.googleusercontent.com",
            'client_secret': "0PF4XcD4jsAKZHFQO1Sf8XPQ",
            'redirect_uri': "https://oauth-194607.appspot.com/oauth",
            'grant_type': 'authorization_code'
            }
        #use urllib in order to send post request
        #https://docs.python.org/2/library/urllib.html
        #concept taken from here
        #https://stackoverflow.com/questions/11322430/how-to-send-post-request
        payload = urllib.urlencode(postBody)
        headers = {'Content-Type':'application/x-www-form-urlencoded'}
        result = urlfetch.fetch(
            url = "https://www.googleapis.com/oauth2/v4/token",
   		 	payload = payload,
    		method = urlfetch.POST,
    		headers = headers)

        conn = json.loads(result.content)
        #debug access tokent
        #self.response.write(json.dumps(conn))
        headers = {'Authorization': 'Bearer ' + conn["access_token"]}
        result = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = headers)

        conn = json.loads(result.content)
        #debug/dump what is in conn in order to see how the googleplus api is formatted
        #self.response.write(json.dumps(conn))
        #for loop that checks if the items in the request has the items needed
        for item in conn:
            if item == 'name':
                checkName = True
            if item == "url":
                checkProfile = True
        #if the items are there then get the needed items from the request
        if checkName == True and checkProfile:
            firstName = conn['name']['givenName']
            lastName = conn['name']['familyName']
            plusLink = str(conn['url'])
            oauthParams = {'firstName': firstName,
                           'lastName': lastName,
                           'plusLink': plusLink,
                           'plusName': "Profile Link",
                           'state': state}
        #Else if the information is not found in the account
        else:
            oauthParams = {'checkAccount': "WARNING: No Google+ account found", 'state': state}
        #write the values to the oauth page
        self.response.out.write(template.render('oauth.html', oauthParams))

#Allowing paatching methods
#Taken from the lecture
#https://stackoverflow.com/questions/16280496/patch-method-handler-on-google-appengine-webapp2
allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods

#Extended routing in order to implement ID's needed for postman
#https://webapp2.readthedocs.io/en/latest/guide/routing.html
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/oauth', OauthHandler)
], debug=True)
