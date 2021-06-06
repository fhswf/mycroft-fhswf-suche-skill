import re
import requests
import json
from mycroft import MycroftSkill, intent_handler
from mycroft.audio import wait_while_speaking
from mycroft.util.parse import extract_number

# change this variable to set a Skill name that does not sound strange in your used language:
SKILL_NAME='FH-SWF Kontaktsuche'

def searchFor(queryName):
    """Queries for a given name within data available at www.fh-swf.de

    Fires up an http post request to the elastic search proxy which is used for global search at the website www.fh-swf.de.
    
    """
    
    fhSwfSearchUrl = 'https://www.fh-swf.de/es_search_proxy/index.php'

    requestHeaders = {'User-Agent': 'Mycroft FhSwfSearchSkill (https://github.com/fhswf/mycroft-fhswf-suche-skill) [2021, Silvio Marra]',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                    }

    queryPayload = {
        "size": 15,
        "query": {
            "bool": {
                "filter": [{"terms": {"content_type.keyword": ["employee"]}}],
                "must": [{"term": {"availableForSearch": {"value": "true"}}},
                {"query_string": {"fields": ["name"], "query": '"' + queryName + '"'}}]}},
        "_source": ["title","first_name","name","email","phone","department","building_room","building_address","building_postalCode","mail_city"],
        "highlight": {"fields": {"name": {}}},
        "track_scores": "true",
        "sort": [{"_score": {"order": "desc"}}]
    }
    
    response = requests.post(fhSwfSearchUrl, data = json.dumps(queryPayload), headers = requestHeaders)
    
    if not response.status_code == 200:
        raise RuntimeError('Could not connect to search proxy at {}, HTTP status code: {}'.format(fhSwfSearchUrl, str(response.status_code)))
    elif not re.search('application/json', response.headers['content-type']):
        raise RuntimeError('Response did not return as json.')
    searchResponse = json.loads(response.text)

    return searchResponse

class FhSwfSearchSkill(MycroftSkill):
    def __init__(self):
        super(FhSwfSearchSkill, self).__init__(name=SKILL_NAME)

    def initialize(self):
        self.register_entity_file('appellation.entity')
        self.register_entity_file('title.entity')
        self.register_entity_file('location.entity')

    def getContactDetailsForPersonByName(self, appellation, name, title,):
        if not name:
            name = self.get_response('did.not.understand.name')
            self.log.info("name is now: " + name)
        
        spelledName = '; '.join(name).upper()

        maxRetries = 2
        while not self.ask_yesno('did.i.recognize.correctly', {'appellation': appellation, 'title': title, 'name': name, 'spelledName': spelledName}) == 'yes' and maxRetries > 0:
            name = self.get_response("please.tell.me.again")
            spelledName = '; '.join(name).upper()
            maxRetries = maxRetries - 1
        
            if maxRetries == 0:
                self.speak_dialog('could.not.understand')
                return -1

        searchResultSet = searchFor(name)

        if searchResultSet['hits']['total']['value'] == 0:
            self.speak_dialog('search.was.not.successful', {'name': name})
            return -1
        
        contacts = list()
        for hit in searchResultSet['hits']['hits']:
            personDetails = hit['_source']
            contacts.append({'title': personDetails['title'],
                             'first_name': personDetails['first_name'],
                             'name': personDetails['name'],
                             'department': personDetails['department'],
                             'phone': personDetails['phone'],
                             'email': personDetails['email'],
                             'building_room': personDetails['building_room'],
                             'building_address': personDetails['building_address'],
                             'building_postalCode': personDetails['building_postalCode'],
                             'mail_city': personDetails['mail_city']
                             })

        cIndex = 0
        if len(contacts) > 1:
            self.speak_dialog('i.found.x.matches', {'matchCount': len(contacts), 'name': name})
            i = 0
            while i < len(contacts):
                wait_while_speaking()
                self.speak_dialog('multiple.matches', {'index': i + 1,
                                                              'title': contacts[i]['title'],
                                                              'first_name': contacts[i]['first_name'],
                                                              'name': contacts[i]['name'],
                                                              'department': contacts[i]['department']
                                                              })
                i += 1
                if i % 2 == 0 and self.ask_yesno('is.your.queried.person.one.of.them') == 'yes':
                    break

            indexResponse = self.get_response('please.tell.me.a.number')
            cIndex = int(extract_number(indexResponse)) - 1

        return {'title': contacts[cIndex]['title'],
                             'first_name': contacts[cIndex]['first_name'],
                             'name': contacts[cIndex]['name'],
                             'department': contacts[cIndex]['department'],
                             'phone': contacts[cIndex]['phone'],
                             'email': contacts[cIndex]['email'],
                             'building_room': contacts[cIndex]['building_room'],
                             'building_address': contacts[cIndex]['building_address'],
                             'building_postalCode': contacts[cIndex]['building_postalCode'],
                             'mail_city': contacts[cIndex]['mail_city']
                             }
    
    @intent_handler('tell.me.about.this.skill.intent')
    def tellMeAboutThisSkill(self, message):
        """Explains how to use this skill if the user asks about how to use it.
        """

        self.log.info(message.serialize())
        return self.speak_dialog('you.can.ask.me.to.find.contact.details.for.a.person')
        

    @intent_handler('which.information.have.you.got.about.person.xyz.intent')
    def handleFullInformationQuery(self, message):
        self.log.info(message.serialize())

        appellation = message.data.get('appellation') or ""
        title = message.data.get('title') or ""
        name = message.data.get('name') or ""

        self.log.info("appellation is:" + str(appellation))
        self.log.info("title is: " + str(title))
        self.log.info("name is: " + str(name))

        contactDetails = self.getContactDetailsForPersonByName(appellation, name, title)
        
        if contactDetails == -1:
            return -1
        
        self.speak_dialog('here.is.the.information.about.person.xyz', {'title': contactDetails['title'],
                                                                       'first_name': contactDetails['first_name'],
                                                                       'name': contactDetails['name']
                                                                       }, wait=True)
        self.speak_dialog('office.location', {'building_room': contactDetails['building_room'],
                                              'building_address': contactDetails['building_address'],
                                              'building_postalCode': ' ' . join(contactDetails['building_postalCode']),
                                              'mail_city': contactDetails['mail_city'],
                                              }, wait=True)
        self.speak_dialog('emailaddress', {'email': contactDetails['email']}, wait=True)
        self.speak_dialog('phonenumber', {'phone': contactDetails['phone']}, wait=True)
        return 0

    @intent_handler('where.do.i.find.person.xyz.intent')
    def handleOfficeQuery(self, message):
        self.log.info(message.serialize())

        appellation = message.data.get('appellation') or ""
        title = message.data.get('title') or ""
        name = message.data.get('name') or ""

        self.log.info("appellation is:" + str(appellation))
        self.log.info("title is: " + str(title))
        self.log.info("name is: " + str(name))

        contactDetails = self.getContactDetailsForPersonByName(appellation, name, title)
        
        if contactDetails == -1:
            return -1
        
        self.speak_dialog('you.can.find.person.xyz.here', {'title': contactDetails['title'],
                                                           'first_name': contactDetails['first_name'],
                                                           'name': contactDetails['name'],
                                                           'building_room': contactDetails['building_room'],
                                                           'building_address': contactDetails['building_address'],
                                                           'building_postalCode': ' ' . join(contactDetails['building_postalCode']),
                                                           'mail_city': contactDetails['mail_city'],
                                                           }, wait=True)
        return 0

    @intent_handler('how.can.i.contact.person.xyz.intent')
    def handleHowToContactQuery(self, message):
        self.log.info(message.serialize())

        appellation = message.data.get('appellation') or ""
        title = message.data.get('title') or ""
        name = message.data.get('name') or ""

        self.log.info("appellation is:" + str(appellation))
        self.log.info("title is: " + str(title))
        self.log.info("name is: " + str(name))

        contactDetails = self.getContactDetailsForPersonByName(appellation, name, title)
        
        if contactDetails == -1:
            return -1
        
        self.speak_dialog('contactdetails.for.person.xyz.are', {'title': contactDetails['title'],
                                                                'first_name': contactDetails['first_name'],
                                                                'name': contactDetails['name'],
                                                                'email': contactDetails['email'],
                                                                'phone': contactDetails['phone']
                                                                }, wait=True)
        return 0

def create_skill():
    return FhSwfSearchSkill()