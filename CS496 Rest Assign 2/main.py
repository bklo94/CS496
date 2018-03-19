#Brandon Lo
#CS496 Rest Assignment 2
#2/4/18

#import modules taken from the lecture video
from google.appengine.ext import ndb
import webapp2
import json
import datetime

#Create the entity model for the boat object
class Boat(ndb.Model):
    name = ndb.StringProperty(required=True)
    type = ndb.StringProperty(required=True)
    length = ndb.IntegerProperty(required=True)
    at_sea = ndb.BooleanProperty(default=True)

#create an entity model that helps keeps track of the departed boats
class departure_history(ndb.Model):
    depature_date = ndb.StringProperty(required=True)
    depBoat = ndb.StringProperty(required=True)

#Create the entity model for the slips
class Slip(ndb.Model):
    number = ndb.IntegerProperty(required=True)
    current_boat = ndb.StringProperty()
    arrival_date = ndb.StringProperty()
    departure_history =  ndb.StructuredProperty(departure_history, repeated=True)

#Main page that just displays my name and the project since there was no requirement
class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('Brandon Lo - REST Planning and Implementation')

#Request Handler for the boat entity
class BoatHandler(webapp2.RequestHandler):
    #Post method for the boat
    def post(self):
        boat_PostData = json.loads(self.request.body)
        #Create a boat with the required data
        #put updates it to the datastore
        #https://cloud.google.com/appengine/docs/standard/python/ndb/modelclass
        #How to creat the entities
        #https://cloud.google.com/appengine/docs/standard/python/ndb/creating-entities
        createBoat = Boat(name=boat_PostData['name'], type=boat_PostData['type'], length=boat_PostData['length'])
        createBoat.put()
        #Create a boat dictionary
        boatDict = createBoat.to_dict()
        #Add a urlsafe in order to retrieve the original entity
        boatDict['self'] = '/boats/' + createBoat.key.urlsafe()
        boatDict['boatID'] = str(createBoat.key.urlsafe())
        #Display the contents of the dictionary
        self.response.write(json.dumps(boatDict))
        self.response.status_int = 201
        self.response.status_message='Boat Created'
    #Get method for the boat
    def get(self, boatID=None):
        #If calling for a single boat
        if boatID:
            #Get the Boat by the urlsafe
            #use of urlsafe to get the entities
            #https://cloud.google.com/appengine/docs/standard/python/ndb/creating-entities
            boatGet = ndb.Key(urlsafe=boatID).get()
            #Convert model to dict
            #https://cloud.google.com/appengine/docs/standard/python/ndb/modelclass#Model_to_dict
            boatDict2 = boatGet.to_dict()
            boatDict2['self'] = '/boats/' + boatID
            boatDict2['boatID'] = str(boatID)
            #Display the contents of the dictionary
            self.response.write(json.dumps(boatDict2))
            self.response.status_int = 201
        #getting a list of boats
        else:
            #Query the boats to get the all entities, so then I can filter it later
            #https://cloud.google.com/appengine/docs/standard/python/ndb/queries
            boats = Boat.query()
            #Create a boat list if not calling for single boat
            boatList = []
            #appending the dictionary boat objects to the boat list
            for boat in boats:
                boatDict3 = boat.to_dict()
                boatDict3['self'] = '/boats/' + boat.key.urlsafe()
                boatDict3['boatID'] = str(boat.key.urlsafe())
                boatList.append(boatDict3)
            #displaying the contents of the boat list
            self.response.write(json.dumps(boatList))
            self.response.status_int = 201
    #delete method of the boat handler
    def delete(self, boatID=None):
        boat = ndb.Key(urlsafe=boatID).get()
        #Create a list for the depatures
        departList = []
        #If the boat key is found
        if boat:
            #grab the slips
            slips = Slip.query()
            for slip in slips:
                print slip.current_boat
                #If the current boat ID is the boatID you want to delete, set it to null
                if boatID == slip.current_boat:
                    slip.current_boat = None
                    #Add the boats to the departure list
                    for ships in slip.departure_history:
                            departList.append(ships)
                    #Set the departure date to today
                    today = datetime.date.today()
                    #Add the depture list of boats to the Depature history class
                    departList.append(departure_history(depature_date=today.strftime("%b-%m-%Y"),depBoat=boat.key.urlsafe()))
                    slip.departure_history = departList
                    slip.arrival_date = None
                    #Set the boat to now be at sea
                    boat.at_sea = True
                    #Update the slip and boat
                    #put tupdates it to the datastore
                    #https://cloud.google.com/appengine/docs/standard/python/ndb/modelclass
                    boat.put()
                    slip.put()
            #delete the boat
            boatKey = boat.key
            boatKey.delete()
            self.response.status_int = 201
            self.response.status_message='Boat Deleted'
            self.response.out.write('Boat Deleted')
        #If the Boat ID was not found then send an error
        else:
            self.response.status_int = 505
            self.response.status_message = "Boat key invalid"
            self.response.out.write('Boat key invalid')
    #patch method for boats
    def patch(self, boatID=None):
        boatPatch = json.loads(self.request.body)
        boat = ndb.Key(urlsafe=boatID).get()
        #If the boat ID was found
        if boat:
            #check what contents want to be modified
            if 'name' in boatPatch:
                boat.name = boatPatch['name']
            elif 'type' in boatPatch:
                boat.type = boatPatch['type']
            elif 'length' in boatPatch:
                boat.length = boatPatch['length']
            #Update the boat
            #put updates it to the datastore
            #https://cloud.google.com/appengine/docs/standard/python/ndb/modelclass
            boat.put()
            boatDict = boat.to_dict()
            boatDict['self'] = '/boats/' + boat.key.urlsafe()
            boatDict['boatID'] = str(boat.key.urlsafe())
            #Dump the contents of the boat out
            self.response.write(json.dumps(boatDict))
            self.response.status_int = 201
        #else if the boat ID was not found, provide an error
        else:
            self.response.status_int = 505
            self.response.status_message ="Boat was not found."
            self.response.out.write('Boat was not found.')
    #put the method of the boat handler
    def put(self, boatID):
        boat_PutData = json.loads(self.request.body)
        boat = ndb.Key(urlsafe=boatID).get()
        #if the boat ID was found
        if boat:
            #update the contents of the boat
            boat.name = boat_PutData['name']
            boat.type = boat_PutData['type']
            boat.length = boat_PutData['length']
            #put updates it to the datastore
            #https://cloud.google.com/appengine/docs/standard/python/ndb/modelclass
            boat.put()
            boatDict = boat.to_dict()
            boatDict['self'] = '/boats/' + boat.key.urlsafe()
            boatDict['boatID'] = str(boat.key.urlsafe())
            self.response.status_int = 201
            self.response.write(json.dumps(boatDict))
        #else if the boat ID was not found, provide an error
        else:
            self.response.status_int = 505
            self.response.status_message ="Boat was not found."
            self.response.out.write('Boat was not found.')

#methods for the slip
class SlipHandler(webapp2.RequestHandler):
    #post method for the slips
    def post(self):
        slipPost = json.loads(self.request.body)
        slips = Slip.query()
        #Create a temp slip to compare to. Create a variable
        tempSlip = slipPost['number']
        slipExists = False
        #If any slip exists
        if slips:
            #check if the slip already has an existing number
            for slip in slips:
                if tempSlip == slip.number:
                    #Since the slips exist, then set the variable to true and break out of the loop
                    slipExists=True
                    break
            #If the variable shows slip exists, send an error message
            if slipExists:
                self.response.status_int = 505
                self.response.status_message ="Slip number already exists"
                self.response.out.write('Slip number already exists')
            #If no existing slip exists, then add a new slip
            else:
                newSlip = Slip(number = slipPost['number'])
                #put updates it to the datastore
                #https://cloud.google.com/appengine/docs/standard/python/ndb/modelclass
                newSlip.put()
                slipDict = newSlip.to_dict()
                slipDict['self'] = '/slips/' + newSlip.key.urlsafe()
                slipDict['slipID'] = str(newSlip.key.urlsafe())
                #Show the contents of the slip
                self.response.write(json.dumps(slipDict))
                self.response.status_int = 201
        #If no slips currently exist, then create a slip
        else:
            newSlip = Slip(number=slipPost['number'])
            #put updates it to the datastore
            #https://cloud.google.com/appengine/docs/standard/python/ndb/modelclass
            newSlip.put()
            slipDict=newSlip.to_dict()
            slipDict['self'] = '/slips/' + newSlip.key.urlsafe()
            slipDict['slipID'] = str(newSlip.key.urlsafe())
            self.response.write(json.dumps(slipDict))
            self.response.status_int = 201
    #Get method for the slips
    def get(self, slipID=None):
        #If the requested slipID was found then get the slip and display it
        if slipID:
            slipGet = ndb.Key(urlsafe=slipID).get()
            slipDict2 = slipGet.to_dict()
            slipDict2['self']='/slips/' + slipID
            slipDict2['slipID'] = str(slipID)
            #Display the slip ID
            self.response.write(json.dumps(slipDict2))
        #If no single slip ID was found, then all the slips are requested
        else:
            #Create a slip list and then append the slip objects to the list
            slips = Slip.query()
            slip_list = []
            for slip in slips:
                slip_dict3=slip.to_dict()
                slip_dict3['self']='/slips/' + slip.key.urlsafe()
                slip_dict3['slipID'] = str(slip.key.urlsafe())
                slip_list.append(slip_dict3)
            #dump the contents of the slip list out
            self.response.write(json.dumps(slip_list))
    #Delete method for the slip handler
    def delete(self, slipID=None):
        slip = ndb.Key(urlsafe=slipID).get()
        #If the slip ID was found, then delete the boat
        if slip:
            #If the slip has a boat inside it, then set it to sea
            if slip.current_boat:
                boat = ndb.Key(urlsafe=slip.current_boat).get()
                boat.at_sea = True
                #put updates it to the datastore
                #https://cloud.google.com/appengine/docs/standard/python/ndb/modelclass
                boat.put()
            #Use of the keys to delete a slip
            #https://cloud.google.com/appengine/docs/standard/python/ndb/creating-entity-keys
            slipKeys = slip.key
            slipKeys.delete()
            #Sent out response that slip was deleted
            self.response.status_int = 201
            self.response.status_message='Slip Deleted'
            self.response.out.write('Slip Deleted')
        #If no slip was found, send an error message
        else:
            self.response.status_int = 505
            self.response.status_message ="Slip key not found or is invalid key"
            self.response.out.write('Slip key not found or is invalid key')
    #Patch method for the slip handler
    def patch(self, slipID=None):
        slipPatch = json.loads(self.request.body)
        slip = ndb.Key(urlsafe=slipID).get()
        #check if any slip exists
        if slip:
            #create a temp slip variable to check if it exists later
            slipsList = Slip.query()
            tempSlip = slipPatch['number']
            slipExists = False
            #if the slip ID is inside the slipsList, then break out of the loop and send an error
            for sID in slipsList:
                if tempSlip == sID.number:
                    slipExists=True
                    break
            #send an error since the slipID does not exist
            if slipExists:
                self.response.status_int = 505
                self.response.status_message ="Slip number already exists"
                self.response.out.write('Slip number already exists')
            #Else if the slipID does not conflict, patch the number
            else:
                if 'number' in slipPatch:
                    slip.number = slipPatch['number']
                #update the new
                #put updates it to the datastore
                #https://cloud.google.com/appengine/docs/standard/python/ndb/modelclass
                slip.put()
                slipDict=slip.to_dict()
                slipDict['self'] = '/slips/' + slip.key.urlsafe()
                slipDict['slipID'] = str(slip.key.urlsafe())
                self.response.write(json.dumps(slipDict))
                self.response.status_int = 201
        #Send an error since there are no existing slips
        else:
            self.response.status_int = 505
            self.response.status_message ="Slip was not found. Invalid key"
            self.response.out.write('Slip was not found.  Invalid key')

#dockhandler for the departure history to check if boat is docked or not
class DockHandler(webapp2.RequestHandler):
    def put(self, slipID=None, boatID=None):
        #Grab the ship and slip Id's
        slip = ndb.Key(urlsafe=slipID).get()
        boat = ndb.Key(urlsafe=boatID).get()
        dockPut = json.loads(self.request.body)
        arrival_date = dockPut['arrival_date']
        #if the slip ID is incorrect send this response
        if not slip:
            self.response.status_int = 405
            self.response.status_message = "Invalid Slip ID"
            self.response.out.write("Invalid Slip ID")
        #if the boat ID is incorrect
        elif not boat:
            self.response.status_int = 404
            self.response.status_message = "Invalid Boat ID"
            self.response.out.write("Invalid Boat ID")
        #if the slip is currently occupied
        elif slip.current_boat:
            self.response.status_int = 403
            self.response.status_message = "Slip is full"
            self.response.out.write("Slip is full")
        #if ship is already docked
        elif boat.at_sea == False:
            self.response.status_int = 402
            self.response.status_message = "Boat already docked"
            self.response.out.write("Boat already docked")
        #else then the boat is allowed to dock
        else:
            #get the key and set the boat to docked
            slip.current_boat = boat.key.urlsafe()
            slip.arrival_date = arrival_date
            boat.at_sea = False
            #update the datastore
            slip.put()
            boat.put()
            #create a temp list
            tempList = []
            #grab the current list of slips
            slipDict=slip.to_dict()
            slipDict['self'] = '/slips/' + slip.key.urlsafe()
            slipDict['slipID'] = str(slip.key.urlsafe())
            slipDict['boat_link'] = "/boats/" + boat.key.urlsafe()
            #append all the slips to the list
            tempList.append(slipDict)
            #now grab all the current boats and append to the list
            boat_dict=boat.to_dict()
            boat_dict['self']='/boats/' + boat.key.urlsafe()
            boat_dict['boatID'] = str(boat.key.urlsafe())
            tempList.append(boat_dict)
            #dump the contents of the list and send a successful response
            self.response.write(json.dumps(tempList))
            self.response.status_int = 201
            self.response.status_message = "Boat successfully docked"
            self.response.out.write("Boat successfully docked")

#Handler to set if the boat is at sea or not
class AtSeaHandler(webapp2.RequestHandler):
    #updates the boat put the boat at sea
    def put(self, boatID=None, slipID=None):
        #Grabs the slip and boat ID's
        slip = ndb.Key(urlsafe=slipID).get()
        boat = ndb.Key(urlsafe=boatID).get()
        temp = json.loads(self.request.body)
        depature_date = temp['depature_date']
        departList = []
        #Check if the Slip ID exists
        if not slip:
            self.response.status_int = 405
            self.response.status_message = "Invalid Slip ID"
            self.response.out.write("Invalid Slip ID")
        #Check if the ship ID exists
        elif not boat:
            self.response.status_int = 404
            self.response.status_message = "Invalid Boat ID"
            self.response.out.write("Invalid Boat ID")
        #Check if the boat is already at sea
        elif boat.at_sea:
            self.response.status_int = 402
            self.response.status_message = "Boat already at sea"
            self.response.out.write("Boat already at sea")
        #If there are no current boats
        elif slip.current_boat is None :
            self.response.status_int = 403
            self.response.status_message = "Slip is empty"
            self.response.out.write("Slip is empty")
        #Else update the slip
        else:
            #set the current ship to none in the slips
            slip.current_boat = None
            #Add all the ships to the departure list
            for ships in slip.departure_history:
                    departList.append(ships)
            #add it to the depature history class
            departList.append(departure_history(depature_date=depature_date, depBoat=boat.key.urlsafe()))
            slip.departure_history = departList
            #set the arrival date to Null and set the ship to at sea
            slip.arrival_date = None
            boat.at_sea = True
            #update the boat and the slip
            #put updates it to the datastore
            #https://cloud.google.com/appengine/docs/standard/python/ndb/modelclass
            boat.put()
            slip.put()
            #create a temporary list and then use it to be dumped to the page
            tempList = []
            #grab the slip objects and add it to the temp list
            slipDict = slip.to_dict()
            slipDict['self'] = '/slips/' + slip.key.urlsafe()
            slipDict['slipID'] = str(slip.key.urlsafe())
            tempList.append(slipDict)
            #grab the boat objects and add it to the temp list
            boatDict = boat.to_dict()
            boatDict['self'] = '/boats/' + boat.key.urlsafe()
            boatDict['boatID'] = str(boat.key.urlsafe())
            tempList.append(boatDict)
            #dump the contents and display the status reponse.
            self.response.write(json.dumps(tempList))
            self.response.status_int = 201
            self.response.status_message="Boat Undocked"
            self.response.out.write("Boat Successfully Undocked")

#Allowing paatching methods
#Taken from the lecture
#https://stackoverflow.com/questions/16280496/patch-method-handler-on-google-appengine-webapp2
allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods

#Extended routing in order to implement ID's needed for postman
#https://webapp2.readthedocs.io/en/latest/guide/routing.html
app = webapp2.WSGIApplication([
    webapp2.Route(r'/', handler=MainPage),
    webapp2.Route(r'/boats', handler=BoatHandler),
    webapp2.Route(r'/boats/<boatID>', handler=BoatHandler),
    webapp2.Route(r'/slips', handler=SlipHandler),
    webapp2.Route(r'/slips/<slipID>', handler=SlipHandler),
    webapp2.Route(r'/slips/<slipID>/dock/<boatID>', handler=DockHandler),
    webapp2.Route(r'/boats/<boatID>/atsea/<slipID>', handler=AtSeaHandler)
], debug=True)
