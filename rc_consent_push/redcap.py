import requests
import json
from flask import current_app
from rc_consent_push import models
from rc_consent_push import db

redcap_url = current_app.config['REDCAP_URL']

class REDCapError(RuntimeError):
    """REDCap connection related errors"""
    pass

def make_project_from_token( token, stu ):
    '''
    For details on the REDCap API methods called in this function see:
    * https://redcap.nubic.northwestern.edu/redcap/api/help/?content=exp_proj 
    '''
    mypayload = dict( format = 'json' )
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
    '''
    For details on the REDCap API methods called in this function see:
    * https://redcap.nubic.northwestern.edu/redcap/api/help/?content=exp_instr 
    '''
    if not isinstance(project, models.Project):
        raise REDCapError(f'Cannot laod instruments because a Project object was not passed')

    mypayload = dict( format = 'json' )
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
    '''
    For details on the REDCap API methods called in this function see:
    * https://redcap.nubic.northwestern.edu/redcap/api/help/?content=exp_instr 
    '''
    if not isinstance(project, models.Project):
        raise REDCapError(f'Cannot laod instruments because a Project object was not passed')

    mypayload = dict( format = 'json' )
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

def fetch_project_fields_as_select2( project ):
    '''
    For details on the REDCap API methods called in this function see:
    * https://redcap.nubic.northwestern.edu/redcap/api/help/?content=exp_metadata 
    '''
    if not isinstance(project, models.Project):
        raise REDCapError(f'Cannot laod instruments because a Project object was not passed')

    mypayload = dict( format = 'json' )
    mypayload['content'] = 'metadata'
    mypayload['token'] = project.api_token
    myrequest = requests.post(redcap_url, mypayload)
    if not myrequest.ok:
        raise REDCapError('REDCap request failed')
    myrequestjson = json.loads(myrequest.text)
    select2_field_array = list()
    select2_field_array.append( dict(id='',text='')) #In single select2 you need first option to be blank to show the placeholder text
    for x in myrequestjson:
        select2_field_array.append( dict(
            id = x['field_name'],
            text = x['field_name']
        ))
    return select2_field_array

def fetch_advanced_link_info ( authkey ):
    '''
    The advanced link feature in project bookmarks only sends an authentication token. You will need to send that back to REDCap to get the other information.
    '''
    mypayload = dict( format = 'json' )
    mypayload['authkey'] = authkey
    myresponse = requests.post(redcap_url, mypayload)
    if not myresponse.ok:
        raise REDCapError('Could not finalize REDCap authentication key validation')
    myresponsejson = json.loads(myresponse.text)

    return myresponsejson

def fetch_advanced_link_records( project, advancedlinkinfo ):
    """
    The function takes as input the information passed from the lookup from redcap.fetch_advanced_link_info()
    Appended to it the record number and the event name passed as part of the URL parameters
    """
    if not isinstance(project, models.Project):
        raise REDCapError(f'Cannot laod instruments because a Project object was not passed')
    mypayload = dict( format = 'json' )
    mypayload['content'] = 'record'
    mypayload['token'] = project.api_token
    if advancedlinkinfo.get( 'get_record', None) is not None: 
        mypayload['records[0]'] = advancedlinkinfo['get_record']
    if advancedlinkinfo.get( 'get_event', None) is not None: 
        mypayload['events[0]'] = advancedlinkinfo['get_event']
    
    myresponse = requests.post(redcap_url, mypayload)
    if not myresponse.ok:
        raise REDCapError('Could not fetch records associated with this project and key')
    myresponsejson = json.loads(myresponse.text)

    return myresponsejson




