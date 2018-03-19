#!/usr/bin/env python
#Brandon Lo
#CS496 Final Project
#2/25/18

'''
You need to implement a REST API
User accounts are supported (ie. there is data tied to specific users that only they can see or modify)
AND the account system uses 3rd party provider, there should be able to be an arbitrary
number of accounts. Accounts *must* have access to some amount of account specific information
that only they can either access or modify.
There should be at least 2 entities and they should have at least 4 properties each
You must also implement one of the following
There should be at least one relationship between entities
It needs to meaningfully use a 3rd party API for something other than authentication
'''

#import modules taken from the lecture video
#implementing template with webapp2, used for the oauth page
#https://webapp2.readthedocs.io/en/latest/tutorials/gettingstarted/templates.html
from google.appengine.ext.webapp import template
from google.appengine.ext import ndb
#using urlfetch to get HTTP requests
#https://cloud.google.com/appengine/docs/standard/python/issue-requests
from google.appengine.api import urlfetch
#randint is used to assign the random movie title
from random import randint
import webapp2
import urllib
#string and random is used to generate the authorization code
import random
import string
import json
import os

#create the movie entity with 6 attributes/properties
class movie(ndb.Model):
    id = ndb.StringProperty()
    movie_id = ndb.StringProperty()
    title = ndb.StringProperty()
    description = ndb.StringProperty()
    release_date = ndb.StringProperty()
    rt_score = ndb.StringProperty()

#create the user account entity with 5 attributes/properties
class userAccount(ndb.Model):
    id = ndb.StringProperty()
    movie_id = ndb.StringProperty()
    fname = ndb.StringProperty()
    lname = ndb.StringProperty()
    email = ndb.StringProperty()

#main page that then gets the authorization code
class MainPage(webapp2.RequestHandler):
    def get(self):
        #logging.debug("The contents of the GET request are:" + repr(self.request.GET))
        #Create a random string for the authorization code
        #https://developers.google.com/actions/identity/oauth2-code-flow
        #How to create a random string with length of 32 needed for the auth code
        #https://stackoverflow.com/questions/37675280/how-to-generate-a-random-string
        #overall the accumulator makes a long url string to send a request
        random_string = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
        url = "https://accounts.google.com/o/oauth2/v2/auth?"
        url = url + "scope=email"
        url = url + "&access_type=offline"
        url = url + "&include_granted_scopes=true"
        url = url + "&state=" + random_string
        url = url + "&redirect_uri=https://oauth-194607.appspot.com/oauth"
        url = url + "&response_type=code"
        url = url + "&client_id=148747034086-cftr2co5d0b8a55edv25a3lear979sqk.apps.googleusercontent.com"
        template_values = {'url': url}
        self.response.out.write(template.render("index.html", template_values))

#oAuth to get the google+ information
class OAuthHandler(webapp2.RequestHandler):
    def get(self):
        #variables used to check if the content requested is avaliable
        movieAccountExists = False
        userAccountExists = False
        auth_code = self.request.GET['code']
        state = self.request.GET['state']
        #How to handle the post code
        #https://developers.google.com/identity/protocols/OAuth2InstalledApp
        post_body = {
            'code': auth_code,
            'client_id': '148747034086-cftr2co5d0b8a55edv25a3lear979sqk.apps.googleusercontent.com',
            'client_secret': 'Exh5PypLuJWmEj-bPWevUq4_',
            'redirect_uri': 'https://oauth-194607.appspot.com/oauth',
            'grant_type': 'authorization_code'
            }
        #use urllib in order to send post request
        #https://docs.python.org/2/library/urllib.html
        #concept taken from here
        #https://stackoverflow.com/questions/11322430/how-to-send-post-request
        payload = urllib.urlencode(post_body)
        headers = {'Content-Type':'application/x-www-form-urlencoded'}
        result = urlfetch.fetch(
            url = "https://www.googleapis.com/oauth2/v4/token",
   		 	payload = payload,
    		method = urlfetch.POST,
    		headers = headers)

        jsonResult = json.loads(result.content)
        #debug access tokent
        #self.response.write(json.dumps(conn))
        headers = {'Authorization': 'Bearer ' + jsonResult['access_token']}
        result = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = headers)
        jsonResult = json.loads(result.content)
        #debug/dump what is in conn in order to see how the googleplus api is formatted
        #self.response.write(json.dumps(conn))
        #for loop that checks if the items in the request has the items needed
        movie_id = jsonResult['id']
        fname = jsonResult['name']['givenName']
        lname = jsonResult['name']['familyName']
        email = jsonResult['emails'][0]['value']
        #if the items are there then get the needed items from the request
        template_values = {'fname': fname,
                           'lname': lname,
                           'movie_id': movie_id}

        result = urlfetch.fetch("https://ghibliapi.herokuapp.com/films/")
        jsonMovies = json.loads(result.content)

        #check if the movie has been associated with the usr
        for user in movie.query():
            if user.movie_id == movie_id:
                movieAccountExists = True

        #check if the user account exists and has a unique ID associated with it
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userAccountExists = True

        #if the user account doesn't exist you create a unique ID and an acccount associated with the user
        if not userAccountExists:
            newUser = userAccount()
            newUser.movie_id = movie_id
            newUser.fname = fname
            newUser.lname = lname
            newUser.email = email
            newUser.put()
            newUser.id = str(newUser.key.urlsafe())
            newUser.put()

        #if the movie has not been associated with the user, a random movie is assigned to the user
        if not movieAccountExists:
            newMovie = movie()
            randomMovie = randint(0,19)
            newMovie.movie_id = movie_id
            newMovie.title = jsonMovies[randomMovie]['title']
            newMovie.description = jsonMovies[randomMovie]['description']
            newMovie.release_date = jsonMovies[randomMovie]['release_date']
            newMovie.rt_score = jsonMovies[randomMovie]['rt_score']
            newMovie.put()
            newMovie.id = str(newMovie.key.urlsafe())
            newMovie.put()

        #dump the relevant information to the oauth html file
        self.response.out.write(template.render("oauth.html", template_values))

#Request Handler for the user entity
class UserHandler(webapp2.RequestHandler):
    #get method for the user
    def get(self, movie_id):
        #variable to check if the user exists
        userExists = False
        #check if a user exists
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userExists = True
        #create a movie list and then associate it with a user's movie_id
        if userExists:
            movieList = []
            movieKey = ""
            #put all of the movie's info and convert it to a dictionary
            #after converting it to dictionary assign it to the movie List
            for movies in movie.query():
                if movies.movie_id == movie_id:
                    movieKey = movies.id
                    getMovie = ndb.Key(urlsafe=movieKey).get()
                    getMovieDict = getMovie.to_dict()
                    getMovieDict['self'] = "/users/" + movie_id + "/movieInfo/" + movies.id
                    movieList.append(getMovieDict)
            #get the user's account's id
            UserAccountKey = ""
            for user in userAccount.query():
                if user.movie_id == movie_id:
                    UserAccountKey = user.id
            #get the user account's key. turn the user info to a dictionary and append it
            getUserAccount = ndb.Key(urlsafe=UserAccountKey).get()
            getUserAccountDict = getUserAccount.to_dict()
            movieList.append(getUserAccountDict)
            #Assign movie_id (unique ID) to the routing method of users
            selfString = "/users/" + movie_id
            selfDict = {"self": selfString}
            #append the routing method and then dump the entire list
            movieList.append(selfDict)
            self.response.write(json.dumps(movieList))
        #if the user doesn't exist, send a 400 response
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist")

#Request Handler for the movie entity
class MovieHandler(webapp2.RequestHandler):
    #get request that gets the movie by ID
    #if the check_id was provided, then the specific movie's infor is returned
    def get(self, movie_id, check_id=None):
        #variable to check if the user exists
        userExists = False
        #for loop that loops through the accounts to check if it exists
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userExists = True
        #if the user exists continue
        if userExists:
            #if movie's unique ID was provided
            if check_id:
                #check if the movie title exists
                movieTitlesExists = False
                for movieInfo in movie.query():
                    if movieInfo.id == check_id:
                        movieTitlesExists = True
                #if the movie title exists, then you can grab the specific info and dump it as a response
                if movieTitlesExists:
                    getMovie = ndb.Key(urlsafe=check_id).get()
                    getMovieDict = getMovie.to_dict()
                    getMovieDict['self'] = "/users/" + movie_id + "/movieInfo/" + check_id
                    self.response.write(json.dumps(getMovieDict))
                #else the movie title/ID doesn't exist and send out an error response
                else:
                    self.response.status = 400
                    self.response.write("ERROR: Movie data does not exist")
            #if no movie's id was given then grab all the movies
            else:
                #fetch the API and load the content
                result = urlfetch.fetch("https://ghibliapi.herokuapp.com/films/")
                jsonMovies = json.loads(result.content)
                averageRTScore = 0.0
                #create a movie list and counter
                movieList = []
                movieKey = ""
                counter = 0
                #for all the movies in the query
                for movies in movie.query():
                    #if it has a user associated with it
                    if movies.movie_id == movie_id:
                        #turn it into a dict and add it to the list
                        movieKey = movies.id
                        getMovie = ndb.Key(urlsafe=movieKey).get()
                        getMovieDict = getMovie.to_dict()
                        getMovieDict['self'] = "/users/" + movie_id + "/movieInfo/" + movies.id
                        movieList.append(getMovieDict)
                        #for all the movies associated with the user, average the rotten tomatoe score
                        for i in range(19):
                            if jsonMovies[i]['title'] == getMovieDict['title']:
                                counter += 1
                                averageRTScore = averageRTScore + float(jsonMovies[i]['rt_score'])
                #create the movie routing for the user
                selfString = "/users/" + movie_id + "/movieInfo"
                selfDict = {"self": selfString}
                #append the route to the list
                movieList.append(selfDict)
                averageRTScore = averageRTScore/counter
                totalMoviesDict = {"averageRTScore": averageRTScore}
                #append the average to the list
                movieList.append(totalMoviesDict)
                #send the entire list as a response
                self.response.write(json.dumps(movieList))
        #else if the movie ID cannot be found, then write an error as a response
        else:
            self.response.status = 400
            self.response.write("ERROR: movies does not exist")

    #Post request that creates a new movie based on the user's movie_id that was inputted
    def post(self, movie_id):
        postData = json.loads(self.request.body)
        #check to see if the user exists
        userExists = False
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userExists = True
        #If the user does exist then call the API
        if userExists:
            result = urlfetch.fetch("https://ghibliapi.herokuapp.com/films/")
            #load the posted data
            jsonMovies = json.loads(result.content)
            #variables that check if the correct input is entered
            #also checks if the movie exists
            #sets the index counter that finds the title
            checkInputName = False
            checkMovieExists = False
            index = 0
            #for loop that looks through the posted data for the title
            for item in postData:
                if item == "title":
                    checkInputName = True
            #if the title was correctly entered, look for the title
            if checkInputName:
                #checks the API response for the correct title and assign the index to the found title's index
                for i in range(19):
                    if jsonMovies[i]['title'] == postData['title']:
                        index = i
                        checkMovieExists = True
                #if the movie exists, then grab the title,description, release_date, and rt_score
                if checkMovieExists:
                    postMovie = movie()
                    #put the API's response information into the datastore
                    postMovie.movie_id = movie_id
                    postMovie.title = jsonMovies[index]['title']
                    postMovie.description = jsonMovies[index]['description']
                    postMovie.release_date = jsonMovies[index]['release_date']
                    postMovie.rt_score = jsonMovies[index]['rt_score']
                    postMovie.put()
                    postMovie.id = str(postMovie.key.urlsafe())
                    postMovie.put()
                    #convert the information to a dict and then write it as a response
                    postMovieDict = postMovie.to_dict()
                    #set up the routing information
                    postMovieDict['self'] = '/users/' + postMovie.movie_id + "/movieInfo/" + postMovie.id
                    self.response.write(json.dumps(postMovieDict))
                #if the movie data could not be found then send a 400 response
                else:
                    self.response.status = 400
                    self.response.write("ERROR: Movie data specified could not be found")
            #if the title format is incorrect, send out the correct format
            else:
                self.response.status = 400
                self.response.write("ERROR: expected format -> {\"title\": \"str\"}")
        #if the user's account cannot be found then send a 400 response
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist")

    #Post request that creates a new movie based on the user's movie_id that was inputted
    def delete(self, movie_id, check_id):
        #checks if a user is associated with the movie
        userExists = False
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userExists = True
        #if the user exists, then check if the movie exists
        if userExists:
            movieTitlesExists = False
            for movieItem in movie.query():
                if movie.id == check_id:
                    movieTitlesExists = True
            if movieTitlesExists:
                #try loop to check if the movie can be deleted
                #https://stackoverflow.com/questions/20731851/how-to-properly-handle-wrong-urlsafe-key-provided
                try:
                    ndb.Key(urlsafe=check_id).delete()
                    self.response.write("SUCCESS: Movie data was deleted")
                #if an error appears, then the movie id does not exist
                except:
                    self.response.status = 400
                    self.response.write("ERROR: Movie data does not exist")
            #the movie does not exist even though the user exists
            else:
                self.response.status = 400
                self.response.write("ERROR: Movie data does not exist")
        #the user doesn't exist therefore send a 400 response
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist")

    #patch method which updates the user depending on method
    def patch(self, movie_id, check_id):
        #load the data that is being sent
        patchData = json.loads(self.request.body)
        #check if the user account exists
        userExists = False
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userExists = True
        #if the user exists
        if userExists:
            #check if the movie's movie_id exists
            movieTitlesExists = False
            for movieItem in movie.query():
                if movieItem.id == check_id:
                    movieTitlesExists = True
            #if the movie exists then get the key
            if movieTitlesExists:
                #if the key doesn't exist/unable to be gotten then send a 400 response
                #https://stackoverflow.com/questions/20731851/how-to-properly-handle-wrong-urlsafe-key-provided
                try:
                    patchMovies = ndb.Key(urlsafe=check_id).get()
                except ProtocolBufferDecodeError:
                    patchMovies = None
                    self.response.status = 400
                    self.response.write("ERROR: Movie data does not exist")
                #if the response isn't correct, trying to patch more than 1 attribute
                #send the correct format expected
                if len(patchData) > 1:
                    self.response.status = 400
                    self.response.write("ERROR: expected format -> {\"title\": \"str\", \"description\": \"str\", \"release_date\": \"str\", \"rt_score\": \"str\"}")
                #else if the format is correct and the movie found
                else:
                    #iterate through the patch data to look ofr the correct attribute to be patched
                    for key in patchData:
                        if key == "title":
                            patchMovies.title = patchData['title']
                            patchMovies.put()
                            self.response.write("SUCCESS: Movie data 'title' was updated")
                        elif key == "description":
                            patchMovies.description = patchData['description']
                            patchMovies.put()
                            self.response.write("SUCCESS: Movie data 'description' was updated")
                        elif key == "release_date":
                            patchMovies.release_date = patchData['release_date']
                            patchMovies.put()
                            self.response.write("SUCCESS: Movie data 'release_date' was updated")
                        elif key == "rt_score":
                            patchMovies.rt_score = patchData['rt_score']
                            patchMovies.put()
                            self.response.write("SUCCESS: Movie data 'rt_score' was updated")
                        #else if the incorrect attribute is attempted to be patched, send the correct format
                        else:
                            self.response.status = 400
                            self.response.write("ERROR: expected format -> {\"title\": \"str\", \"description\": \"str\", \"release_date\": \"str\", \"rt_score\": \"str\"}")
            #if the movie doesn't exist then send a 400 response
            else:
                self.response.status = 400
                self.response.write("ERROR: Movie data does not exist")
        #if the user doesn't exist then send a 400 response
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist")

    #put method which changes and entire movie's info
    def put(self, movie_id, check_id):
        putData = json.loads(self.request.body)
        #check if the user account exists
        userExists = False
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userExists = True
        #if the user account exists then check if the movie exists
        if userExists:
            movieTitlesExists = False
            #iterate through the movie datastore and check if the movie exists
            for movieItem in movie.query():
                if movieItem.id == check_id:
                    movieTitlesExists = True
            #if the movie exists then check all the input
            if movieTitlesExists:
                putMovieInfo = ndb.Key(urlsafe=check_id).get()
                checkInputName = False
                inputDescription = False
                inputReleaseDate = False
                inputRTScore = False
                #check all the attribute inputs
                for item in putData:
                    if item == "title":
                        checkInputName = True
                    elif item == "description":
                        inputDescription = True
                    elif item == "release_date":
                        inputReleaseDate = True
                    elif item == "rt_score":
                        inputRTScore = True
                #if all attribute inputs are valid then put them into a response
                if checkInputName and inputDescription and inputReleaseDate and inputRTScore:
                    putMovieInfo.title = putData['title']
                    putMovieInfo.description = putData['description']
                    putMovieInfo.release_date = putData['release_date']
                    putMovieInfo.rt_score = putData['rt_score']
                    putMovieInfo.put()
                    #write all the put data as a response
                    self.response.write("SUCCESS: Movie data 'title', 'description', 'release_date', and 'rt_score' were updated")
                #else if the inputted data was incorrect, then send out the correct format
                else:
                    self.response.status = 400
                    self.response.write("ERROR: expected format -> {\"title\": \"str\", \"description\": \"str\", \"release_date\": \"str\", \"rt_score\": \"str\"}")
            #if the movie isn't found then send a 400 response
            else:
                self.response.status = 400
                self.response.write("ERROR: Movie data does not exist")
        #if the user isn't found then send a 400 response
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist")

#Request Handler for the movie entity
class UserAccountHandler(webapp2.RequestHandler):
    #get method to get the user's account info by ID
    def get(self, movie_id):
        #check to see if the user exists. If they exist grab the account key
        userAccountExists = False
        UserAccountKey = ""
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userAccountExists = True
                UserAccountKey = user.id
        #if the account exists, use the key to get the account info and turn it into a dict
        if userAccountExists:
            getUserAccount = ndb.Key(urlsafe=UserAccountKey).get()
            getUserAccountDict = getUserAccount.to_dict()
            #set the correct route and then dump it as a response
            getUserAccountDict['self'] = "/users/" + movie_id + "/accountinfo"
            self.response.write(json.dumps(getUserAccountDict))
        #else the user account wasn't found
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist")
    #delete the user based on the id
    def delete(self, movie_id):
        #check to see if the user exists. If they exist grab the account key
        userAccountExists = False
        UserAccountKey = ""
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userAccountExists = True
                UserAccountKey = user.id
        #if the user exists then delete the user
        if userAccountExists:
            ndb.Key(urlsafe=UserAccountKey).delete()
            #once the user is deleted, delete all the movies associated with the user
            for user in movie.query():
                if user.movie_id == movie_id:
                    movieKey = user.id
                    ndb.Key(urlsafe=movieKey).delete()
            #once the user and all the movies are deleted, then send a successful response
            self.response.write("SUCCESS: User's account was deleted")
        #else if the user isn't found then send a 400 response
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist")

    #patch method to patch a user based on the response
    def patch(self, movie_id):
        #grab the response and load it
        patchData = json.loads(self.request.body)
        #check to see if the user exists. If they exist grab the account key
        userAccountExists = False
        UserAccountKey = ""
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userAccountExists = True
                UserAccountKey = user.id
        #if the user exists then check the patch method format
        if userAccountExists:
            patchUser = ndb.Key(urlsafe=UserAccountKey).get()
            #if the patch method is trying to patch more than 1 attribute, then send the correct formatting
            if len(patchData) > 1:
                self.response.status = 400
                self.response.write("ERROR: expected format -> {\"fname\": \"str\"} or {\"lname\": \"str\"} or {\"email\": \"str\"}")
            #else if the patch has the correct attributes
            else:
                #iterate through the request for the correct attribute to patch
                #once the correct attribute is found write a response
                for key in patchData:
                    if key == "fname":
                        patchUser.fname = patchData['fname']
                        patchUser.put()
                        self.response.write("SUCCESS: User 'fname' was updated")
                    elif key == "lname":
                        patchUser.lname = patchData['lname']
                        patchUser.put()
                        self.response.write("SUCCESS: User 'lname' was updated")
                    elif key == "email":
                        patchUser.email = patchData['email']
                        patchUser.put()
                        self.response.write("SUCCESS: User 'email' was updated")
                    #else if the attribute isn't listed, then send the correct formatting
                    else:
                        self.response.status = 400
                        self.response.write("ERROR: expected format -> {\"fname\": \"str\"} or {\"lname\": \"str\"} or {\"email\": \"str\"}")
        #if the user doesn't exist send a 400 response
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist")

    #put response based on the user's id
    def put(self, movie_id):
        #check to see if the user exists. If they exist grab the account key
        putData = json.loads(self.request.body)
        userAccountExists = False
        UserAccountKey = ""
        for user in userAccount.query():
            if user.movie_id == movie_id:
                userAccountExists = True
                UserAccountKey = user.id
        #if the account exists
        if userAccountExists:
            putUser = ndb.Key(urlsafe=UserAccountKey).get()
            #variables to check the response
            inputFname = False
            inputLname = False
            inputEmail = False
            #if the account exists, check if the request has the correct format
            for item in putData:
                if item == "fname":
                    inputFname = True
                elif item == "lname":
                    inputLname = True
                elif item == "email":
                    inputEmail = True
            #if the items are there then get the needed items from the request
            if inputFname and inputLname and inputEmail:
                putUser.fname = putData['fname']
                putUser.lname = putData['lname']
                putUser.email = putData['email']
                putUser.put()
                self.response.write("SUCCESS: User 'fname', 'lname', and 'email' were updated")
            #else then the formatting is correct and the correct format is send
            else:
                self.response.status = 400
                self.response.write("ERROR: expected format -> {\"fname\": \"str\", \"lname\": \"str\", \"email\": \"str\"}")
        #else the user doesn't exist and a 400 response is sent as the status
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist")

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
    ('/oauth',OAuthHandler),
    ('/users/(.*)/movieInfo/(.*)',MovieHandler),
    ('/users/(.*)/movieInfo',MovieHandler),
    ('/users/(.*)/accountinfo',UserAccountHandler),
    ('/users/(.*)',UserHandler)
], debug=True)
