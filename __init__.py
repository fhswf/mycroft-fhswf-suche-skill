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

    Fires up an http post request to the elastic search proxy which is used for global search at the website www.fh-swf.de/de/search/search.php.
    The query is set up to filter by employees and using the surname as query for the field "name".
    It returns a 'hits' array in the response which also has a 'hits' array - sorted by '_score' value. 
    
    Parameters
    ----------
    queryName: string
        The surname of a person to look for.

    Returns
    -------
    searchResponse: dict
        Elasticsearch response as dict.
    """
    
    fhSwfSearchUrl = 'https://www.fh-swf.de/es_search_proxy/index.php'

    requestHeaders = {'User-Agent': 'Mycroft FhSwfSearchSkill (https://github.com/fhswf/mycroft-fhswf-suche-skill) [2021, Silvio Marra]',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                    }
    """Due to a change how the FH-SWF CMS queries the ElasticSearch, the payload needs to be fixed. Following solution is TEMPORARILY for the presentation at the "Kolloquium"
       and gets fixed, soon after.
    """
    # queryPayload = {
    #     "size": 15,
    #     "query": {
    #         "bool": {
    #             "filter": [{"terms": {"content_type.keyword": ["employee"]}}],
    #             "must": [{"term": {"availableForSearch": {"value": "true"}}},
    #             {"query_string": {"fields": ["name"], "query": '"' + queryName + '"'}}]}},
    #     "_source": ["title","first_name","name","email","phone","department","building_room","building_address","building_postalCode","mail_city"],
    #     "highlight": {"fields": {"name": {}}},
    #     "track_scores": "true",
    #     "sort": [{"_score": {"order": "desc"}}]
    # }

    queryPayload = {
        "highlight": {
            "pre_tags": ["<strong>"],
            "post_tags": ["</strong>"],
            "fields": [{
                "title": {
                    "number_of_fragments": 5,
                    "no_match_size": 100,
                    "fragment_size": 100
                }
            }, {
                "short_text": {
                    "number_of_fragments": 5,
                    "no_match_size": 300,
                    "fragment_size": 300
                }
            }]
        },
        "size": 10,
        "query": {
            "function_score": {
                "functions": [{
                    "filter": {
                        "match": {
                            "target": "studierende"
                        }
                    },
                    "weight": 1.3
                }, {
                    "filter": {
                        "match": {
                            "target": "studieninteressierte"
                        }
                    },
                    "weight": 1.3
                }, {
                    "filter": {
                        "match": {
                            "content_type": "press_archives"
                        }
                    },
                    "weight": 0.5
                }],
                "score_mode": "sum",
                "query": {
                    "bool": {
                        "filter": [{
                            "terms": {
                                "content_type.keyword": ["employee"]
                            }
                        }, {
                            "terms": {
                                "langCode.keyword": ["DE"]
                            }
                        }],
                        "must": [{
                            "term": {
                                "availableForSearch": {
                                    "value": "true"
                                }
                            }
                        }, {
                            "query_string": {
                                "fields": ["title^2.0", "keywords^2.0", "short_text^1.5", "details_text", "section_headline", "section.infobox", "section.chart_teaser", "section.accordeon^0.5",
                                    "section.content^0.5", "section.content_table^0.5", "model", "areasofexpertise", "subexpertise", "degree", "firstsemester", "content", "heading", "sub_heading",
                                    "abstract", "message", "attachment.title", "attachment.keywords", "first_name", "name", "department", "mail_city"
                                ],
                                "query": queryName,
                                "default_operator": "AND",
                                "allow_leading_wildcard": "true"
                            }
                        }]
                    }
                }
            }
        },
        "_source": ["first_name", "name", "email", "phone", "department", "building_room", "building_address", "building_postalCode", "mail_city", "title", "short_text", "websiteUrl",
            "breadcrumb", "internal", "content_type", "target", "heading", "sub_heading", "published", "abstarct", "message", "location", "date"
        ],
        "from": 0,
        "sort": [{
            "_score": {
                "order": "desc"
            }
        }],
        "aggs": {
            "filter.content_type": {
                "terms": {
                    "field": "content_type.keyword",
                    "size": 100,
                    "missing": "",
                    "min_doc_count": 0,
                    "order": {
                        "_key": "asc"
                    }
                }
            },
            "filter.location": {
                "terms": {
                    "field": "location.keyword",
                    "size": 100,
                    "missing": "",
                    "min_doc_count": 0,
                    "order": {
                        "_key": "asc"
                    }
                }
            },
            "filter.target": {
                "terms": {
                    "field": "target.keyword",
                    "size": 100,
                    "missing": "",
                    "min_doc_count": 0,
                    "order": {
                        "_key": "asc"
                    }
                }
            }
        }
    }
    """TMP-HOTFIX END"""

    response = requests.post(fhSwfSearchUrl, data = json.dumps(queryPayload), headers = requestHeaders)
    
    if not response.status_code == 200:
        raise RuntimeError('Could not connect to search proxy at {}, HTTP status code: {}'.format(fhSwfSearchUrl, str(response.status_code)))
    elif not re.search('application/json', response.headers['content-type']):
        raise RuntimeError('Response did not return as json.')
    searchResponse = json.loads(response.text)

    return searchResponse

class FhSwfSearchSkill(MycroftSkill):
    """FhSwfSearchSkill provides mycroft with the ability to query for contact information of employees and lecturers.

    It utilizes the current search proxy which is used within the website at www.fh-swf.de/de/search/search.php for Elasticsearch.
    to query for a surname of a person, to handle queries to obtain contact information of employees and lecturers.
    """

    def __init__(self):
        super(FhSwfSearchSkill, self).__init__(name=SKILL_NAME)

    def initialize(self):
        """Skill setup after initialization with Mycroft.

        Registers entity files used by the skill.
        """

        self.register_entity_file('appellation.entity')
        self.register_entity_file('title.entity')
        self.register_entity_file('location.entity')

    def getContactDetailsForPersonByName(self, appellation, name, title):
        """Calls the searchFor() function to generate a response to a contact query to speak from Mycroft.
        Before calling searchFor() spells the name back to the user, to get confirmation if it is the right query string.
        If not, the user can retry to pass the name. This happens 2 times at max. After that, the Skill will exit with a 
        failure message.

        If the resultset has more than one result for a surname because more people have the same surname, then we speak the first two
        and asks if the queried person was one of the two. If not, the next 2 will be spoken and again a yes-no question will be triggered.
        
        Parameters
        ----------
        apellation: string
            The appellation before academic title from queried name, due to german grammar. In this case herr, herrn or frau from appellation.entity
            (e.g. Herr Professor Dr.). Used to speak a whole title of a person's name.

        name: string
            Surname of the lecturer or employee to look for.

        title: string
            Academic title which comes from the query, to speak it together with name (like appellation).

        Returns
        -------
        dictionary: dict
            A dictionary containing contact details of the queried person or -1 if query was unsuccessful or / and therefore empty.
        """

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
        """Handles the query for a full output of contact details of a person.
        """

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
        """Handles the query for where to find a persons office / location.
        """

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
        """Handles the query for a persons contact data (phone number and email address).
        """
        
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