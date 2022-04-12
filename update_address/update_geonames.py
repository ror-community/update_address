import requests
import json
from copy import deepcopy

GEONAMES = {}
GEONAMES['USER'] = "roradmin"
GEONAMES['URL'] = 'http://api.geonames.org/getJSON'

def ror_geonames_mapping():
    # contains either default null values or mapping to geonames response
    template = {
      "lat": "lat",
      "lng": "lng",
      "state": None,
      "state_code": None,
      "country_geonames_id": "countryId",
      "city": "name",
      "geonames_city": {
        "id": "geonameId",
        "city": "name",
        "geonames_admin1": {
            "name": "adminName1",
            "ascii_name": "adminName1",
            "id": "adminId1",
            "code": ["countryCode","adminCode1"]
        },
        "geonames_admin2": {
            "name": "adminName2",
            "id": "adminId2",
            "ascii_name": "adminName2",
            "code": ["countryCode","adminCode1","adminCode2"]
        },
        "nuts_level1": {
            "name": None,
            "code": None
        },
        "nuts_level2": {
            "name": None,
            "code": None
        },
        "nuts_level3": {
            "name": None,
            "code": None
        }
      }
    }
    return template

def get_geonames_response(id):
    # queries geonames api with the location geonames id as a query parameter
    print("Fetching Geonames ID " + str(id))
    msg = None
    result = None
    query_params = {}
    query_params['geonameId'] = id
    query_params['username'] = GEONAMES['USER']
    url = GEONAMES['URL']
    try:
        response = requests.get(url,params=query_params)
        response.raise_for_status()
        result = json.loads(response.text)
    except requests.exceptions.HTTPError as errh:
        msg = "Http Error: " + str(errh)
        print (msg)
    except requests.exceptions.ConnectionError as errc:
        msg = "Error Connecting: " + str(errc)
        print (msg)
    except requests.exceptions.Timeout as errt:
        msg = "Timeout Error: " + str(errt)
        print (msg)
    except requests.exceptions.RequestException as err:
        msg = "Request exception: " + str(err)
        print (msg)
    return result,msg

def field_types(key):
    types = {
        "lat": "convert_float",
        "lng": "convert_float",
        "id": "convert_integer",
        "country_geonames_id": "convert_integer"
    }
    return types.get(key, None)

def convert_integer(value):
    return int(value)

def convert_float(value):
    return float(value)

def compare_ror_geoname(mapped_fields,ror_address,geonames_response, original_address):
    for key, value in mapped_fields.items():
        # If value is of dict type then print
        # all key-value pairs in the nested dictionary
        if isinstance(value, dict):
            if key in ror_address:
                # nuts_levelX values were formatted as nuts_level1: None
                # in new records added Mar 2022 release
                # existing records were formmated as nuts_level1: {'code': None, 'name': None}
                # check and update empty nuts data to match existing records
                # OK to remove when Mar 2022 records have been corrected
                if "nuts_level" in key:
                    if ror_address[key] is None:
                        ror_address[key] = value
                else:
                    compare_ror_geoname(value,ror_address[key],geonames_response, original_address)
        else:
            ror_value = ror_address[key] if key in ror_address else original_address[key]
            geonames_value = None
            if (key == "code" and value):
                key_exists = True
                for x in value:
                    if not(x in geonames_response):
                        key_exists = False
                if key_exists:
                    geonames_value = ".".join([geonames_response[x] for x in value])
            elif (value in geonames_response) and (geonames_response[value] != ""):
                geonames_value = geonames_response[value]
            if ((str(ror_value) != str(geonames_value))) and geonames_value:
                check_type = field_types(key)
                if check_type:
                    # metaprogramming below.
                    # The value of the dictionary is the same as the function name
                    #globals keeps a dictionary of all symbols here and can be run as a function.
                    ror_address[key] = globals()[check_type](geonames_value)
                else:
                    ror_address[key] = geonames_value
            elif (not(value) or not(geonames_value)):
                # if value is set to Null or there is no key present in geonames response that is mapped to the ror key. For ex: there is no geonames admin 2 information
                ror_address[key] = None

    return deepcopy(ror_address)

def compare_countries(record, geonames_response):
    geonames_country_name, geonames_country_code = geonames_response[
        'countryName'], geonames_response['countryCode']
    if record['country']['country_code'] != geonames_country_code:
        record['country']['country_name'] = geonames_country_name
        record['country']['country_code'] = geonames_country_code
    return record

def get_record_address(record):
    # returns the address dictionary with the geonames city id
    address = record['addresses'][0]
    id = address['geonames_city']['id']
    return id,address

def update_geonames(record, alt_id=None):
    print("Updating Geonames info for record: " + record["id"])
    id, ror_address = get_record_address(record)
    if alt_id:
        id = alt_id
    geonames_response = get_geonames_response(id)[0]
    try:
        mapped_fields = ror_geonames_mapping()
        address = compare_ror_geoname(mapped_fields, ror_address, geonames_response, ror_address)
        record['addresses'][0] = address
        record = compare_countries(record, geonames_response)
        return record
    except:
        print("Could not update Geonames ID " + str(id) + " for record " + str(record["id"]))