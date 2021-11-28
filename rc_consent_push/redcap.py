import requests
import json
from flask import current_app
from rc_consent_push import models
from rc_consent_push import db

redcap_url = current_app.config['REDCAP_URL']
_payload_skel = dict( format = 'json')

class REDCapError(RuntimeError):
    """REDCap connection related errors"""
    pass

def make_project_from_token( token, stu ):
    mypayload = _payload_skel
    mypayload['content'] = 'project'
    mypayload['token'] = token

    myrequest = requests.post(redcap_url, mypayload)
    if not myrequest.ok:
        raise REDCapError('REDCap request failed')
    
    myrequestjson = json.loads(myrequest.text)
    
    myproject = models.Project(
        pid = myrequestjson.get('project_id', None),
        project_title = myrequestjson.get('project_title', None),
        api_token = token,
        stu = stu,
        is_longitudinal = myrequestjson.get('is_longitudinal', None),
        has_repeating_instruments_or_events = myrequestjson.get('has_repeating_instruments_or_events', None),
        surveys_enabled = myrequestjson.get('surveys_enabled', None)
    )

    return myproject

def fetch_project_instruments( project ):
    if not isinstance(myproject, models.Project):
        raise REDCapError(f'Cannot laod instruments because a Project object was not passed')

    mypayload = _payload_skel
    mypayload['content'] = 'instrument'
    mypayload['token'] = project.api_token
    myrequest = requests.post(redcap_url, mypayload)
    if not myrequest.ok:
        raise REDCapError('REDCap request failed')
    myrequestjson = json.loads(myrequest.text)

    myinstruments = list()
    for myinstrument in myrequestjson:
        myinstruments.append( models.Instrument (
            pid = project.pid,
            instrument_name = myinstrument['instrument_name'],
            instrument_label = myinstrument['instrument_label']
        ))

    return myinstruments # Returns them as objects in partial ORM bind

def fetch_project_instruments_as_select2( project ):
    if not isinstance(project, models.Project):
        raise REDCapError(f'Cannot laod instruments because a Project object was not passed')

    mypayload = _payload_skel
    mypayload['content'] = 'instrument'
    mypayload['token'] = project.api_token
    myrequest = requests.post(redcap_url, mypayload)
    if not myrequest.ok:
        raise REDCapError('REDCap request failed')
    myrequestjson = json.loads(myrequest.text)
    select2_instrument_array = list()
    select2_instrument_array.append( dict(id='',text='')) #In single select2 you need first option to be blank to show the placeholder text
    for x in myrequestjson:
        select2_instrument_array.append( dict(
            id = x['instrument_name'],
            text = x['instrument_label']
        ))
    return select2_instrument_array

