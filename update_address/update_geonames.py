import requests
import json
from copy import deepcopy

GEONAMES = {}
GEONAMES['USER'] = "roradmin"
GEONAMES['URL'] = 'http://api.geonames.org/getJSON'
CONVERT_FLOAT = 'convert_float'
CONVERT_INT = 'convert_integer'
RESPONSE_CACHE = {}
CONTINENT_CODES_NAMES = {
    "AF": "Africa",
    "AN": "Antarctica",
    "AS": "Asia",
    "EU": "Europe",
    "NA": "North America",
    "OC": "Oceania",
    "SA": "South America"
}

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

def ror_geonames_mapping_v2():
    # contains either default null values or mapping to geonames response
    template = {
      "geonames_id": "geonameId",
      "geonames_details": {
            "continent_code": "continentCode",
            "country_code": "countryCode",
            "country_name": "countryName",
            "country_subdivision_code": ["adminCodes1", "ISO3166_2"],
            "country_subdivision_name": "adminName1",
            "lat": "lat",
            "lng": "lng",
            "name": "name"
      }
    }
    return template

def ror_empty_address(geonames_id):
    ror_address = {
      "lat": None,
      "lng": None,
      "state": None,
      "state_code": None,
      "country_geonames_id": None,
      "city": None,
      "geonames_city": {
        "id": geonames_id,
        "city": None,
        "geonames_admin1": {
            "name": None,
            "ascii_name": None,
            "id": None,
            "code": None
        },
        "geonames_admin2": {
            "name": None,
            "id": None,
            "ascii_name": None,
            "code": None
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
    return ror_address

def ror_empty_location_v2(geonames_id):
    ror_address = {
      "geonames_id": convert_integer(geonames_id),
      "geonames_details": {
        "continent_code": None,
        "continent_name": None,
        "country_code": None,
        "country_name": None,
        "country_subdivision_code": None,
        "country_subdivision_name": None,
        "lat": None,
        "lng": None,
        "name": None
      }
    }
    return ror_address

def ror_empty_country():
    ror_country = {
            "country_code": None,
            "country_name": None,
    }
    return ror_country

def get_geonames_response(id):
    print("Fetching Geonames ID " + str(id))
    # queries geonames api with the location geonames id as a query parameter
    msg = None
    result = None
    query_params = {}
    query_params['geonameId'] = id
    query_params['username'] = GEONAMES['USER']
    url = GEONAMES['URL']
    if id in RESPONSE_CACHE:
        result = RESPONSE_CACHE[id]
    else:
        try:
            response = requests.get(url,params=query_params)
            response.raise_for_status()
            result = json.loads(response.text)
            RESPONSE_CACHE[id] = result
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

def field_types(key, geonames_value):
    types = {
        "lat": CONVERT_FLOAT,
        "lng": CONVERT_FLOAT,
        "id": CONVERT_INT,
        "country_geonames_id": CONVERT_INT
    }
    if(key == "lat" or key == "lng"):
        if geonames_value != None and "." not in geonames_value:
            types[key] = CONVERT_INT

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
                # in new records added in Mar 2022 release empty nuts_levelX values were formatted like
                # nuts_level1: None
                # existing records were formatted like
                # nuts_levelX: {'code': None, 'name': None}
                # check and update empty nuts_levelX fields to match existing records
                # OK to remove when Mar 2022 records have been corrected
                if "nuts_level" in key and ror_address[key] is None:
                    ror_address[key] = value
                else:
                    # in new records added in Mar 2022 release empty geonames_adminX values were formatted like
                    # geonames_adminX: None
                    # existing records were formatted like
                    # "geonames_adminX": {"ascii_name": null,"id": null,"name": null,"code": null}
                    # check and update empty geonames_adminX fields to match existing records
                    # OK to remove when Mar 2022 records have been corrected
                    if "geonames_admin" in key and ror_address[key] is None:
                        ror_address[key] = value
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
                check_type = field_types(key, geonames_value)
                if check_type:
                    # metaprogramming below.
                    # The value of the dictionary is the same as the function name
                    # globals keeps a dictionary of all symbols here and can be run as a function.
                    ror_address[key] = globals()[check_type](geonames_value)
                else:
                    ror_address[key] = geonames_value
            elif (not(value) or not(geonames_value)):
                # if value is set to Null or there is no key present in geonames response that is mapped to the ror key. For ex: there is no geonames admin 2 information
                ror_address[key] = None

    return deepcopy(ror_address)

def compare_ror_geoname_v2(mapped_fields,ror_location,geonames_response,original_location):
    for key, value in mapped_fields.items():
        # If value is of dict type then print
        # all key-value pairs in the nested dictionary
        if isinstance(value, dict):
            if key in ror_location:
                compare_ror_geoname(value,ror_location[key],geonames_response,original_location)
        else:
            ror_value = ror_location[key] if key in ror_location else original_location[key]
            geonames_value = None
            if key == 'country_subdivision_code':
                if value[0] in geonames_response:
                    if geonames_response[value[0]][value[1]] != "":
                        geonames_value = geonames_response[value[0]][value[1]]
            else:
                if (value in geonames_response) and (geonames_response[value] != ""):
                    geonames_value = geonames_response[value]
            if ((str(ror_value) != str(geonames_value))) and geonames_value:
                check_type = field_types(key, geonames_value)
                if check_type:
                    # metaprogramming below.
                    # The value of the dictionary is the same as the function name
                    # globals keeps a dictionary of all symbols here and can be run as a function.
                    ror_location[key] = globals()[check_type](geonames_value)
                else:
                    ror_location[key] = geonames_value
            elif (not(value) or not(geonames_value)):
                # if value is set to Null or there is no key present in geonames response that is mapped to the ror key. For ex: there is no geonames admin 2 information
                ror_location[key] = None
    return deepcopy(ror_location)

def compare_countries(record, geonames_response):
    geonames_country_name, geonames_country_code = geonames_response[
        'countryName'], geonames_response['countryCode']
    if record['country']['country_code'] != geonames_country_code:
        record['country']['country_name'] = geonames_country_name
        record['country']['country_code'] = geonames_country_code
    elif record['country']['country_code'] == geonames_country_code and record['country']['country_name'] != geonames_country_name:
        record['country']['country_name'] = geonames_country_name
    return record

def fill_new_country(ror_country, geonames_response):
    geonames_country_name, geonames_country_code = geonames_response[
        'countryName'], geonames_response['countryCode']
    ror_country['country_name'] = geonames_country_name
    ror_country['country_code'] = geonames_country_code
    return ror_country

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

def update_geonames_v2(record, alt_id=None):
    print("Updating Geonames info for record: " + record["id"])
    updated_locations = []
    mapped_fields = ror_geonames_mapping_v2()
    #try:
        for location in record['locations']:
            #try:
            geonames_response = get_geonames_response(location['geonames_id'])[0]
            print("Geonames response:")
            print(geonames_response)
            updated_location = compare_ror_geoname(mapped_fields, location, geonames_response, location)
            if updated_location['geonames_details']['continent_code']:
                updated_location['geonames_details']['continent_name'] = CONTINENT_CODES_NAMES[updated_location['geonames_details']['continent_code']]
            print("Updated location:")
            print(updated_location)
            updated_locations.append(updated_location)
            #except:
            #    print("Could not update Geonames ID " + location['geonames_id'] + " for record " + str(record["id"]))

        record['locations'] = deepcopy(updated_locations)
        return record
    #except:
    #    print("Could not update locations for record " + str(record["id"]))

def new_geonames(geonames_id):
    response = {}
    print("Getting Geonames info for ID: " + geonames_id)
    geonames_response = get_geonames_response(geonames_id)[0]
    ror_address = ror_empty_address(geonames_id)
    ror_country = ror_empty_country()
    try:
        mapped_fields = ror_geonames_mapping()
        address = compare_ror_geoname(mapped_fields, ror_address, geonames_response, ror_address)
        country = fill_new_country(ror_country, geonames_response)
        response['address'] = address
        response['country'] = country
        return response
    except:
        print("Could not create ROR address for Geonames ID " + str(geonames_id))

def new_geonames_v2(geonames_id):
    response = {}
    print("Getting Geonames info for ID: " + geonames_id)
    geonames_response = get_geonames_response(geonames_id)[0]
    ror_location = ror_empty_location_v2(geonames_id)
    try:
        mapped_fields = ror_geonames_mapping_v2()
        location = compare_ror_geoname_v2(mapped_fields, ror_location, geonames_response, ror_location)
        if location['geonames_details']['continent_code']:
            location['geonames_details']['continent_name'] = CONTINENT_CODES_NAMES[location['geonames_details']['continent_code']]
        response['location'] = location
        return response
    except:
        print("Could not create ROR address for Geonames ID " + str(geonames_id))

