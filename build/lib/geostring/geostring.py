import collections
import csv
import editdistance as ed
import os
import pandas as pd
import re
from unidecode import unidecode
        
def get_geo_info(geo_input='',
                 re_sub='',
                 loc_index=None):
    geo_input_pp = re.sub(re_sub,'',unidecode(geo_input).lower().strip())
    curr_match = (None,1000)
    
    for i in loc_index:
        ed_match = ed.eval(geo_input_pp,i)
        if ed_match < curr_match[1]:
            curr_match = (i,ed_match)
    geodict = collections.OrderedDict(
        {'geo_input':geo_input,
        'geo_input_pp':geo_input_pp,
        'geo_input_match':curr_match[0],
        'geo_city':loc_index[curr_match[0]][0],
        'geo_subcountry':loc_index[curr_match[0]][1],
        'geo_country':loc_index[curr_match[0]][2],
        'ed_best_match':curr_match[1],
        'ed_tolerance':curr_match[1]/max([len(geo_input_pp),len(curr_match[0])])})
    return geodict
    
def resolve(loc_string,max_tolerance=0.25,verbose=False):
    geostring = Geostring(loc_string)
    for i in geostring.results:
        if i['ed_tolerance'] > max_tolerance:
            if verbose == True:
                print('Tolerance between "' + i['geo_input'] + '" and "' + i['geo_input_match'] + '" (' + str(i['ed_tolerance']) + ') equals or exceeds max tolerance of',max_tolerance,'; removing...')
    geostring.results = [i for i in geostring.results if i['ed_tolerance'] <= max_tolerance]
                
    if geostring.results == []:
        if verbose == True:
            print('No results, Geostring object empty...')
        return
    else:
        resolved_location = collections.OrderedDict({'resolved_city':'','resolved_subcountry':'','resolved_country':''})
        if len(geostring.results) == 1:
            resolved_location['resolved_city'] = geostring.results[0]['geo_city']
            resolved_location['resolved_subcountry'] = geostring.results[0]['geo_subcountry']
            resolved_location['resolved_country'] = geostring.results[0]['geo_country']
            return resolved_location
        else:        
            all_locs = []
            all_locs.append([i['geo_city'] for i in geostring.results])
            all_locs.append([i['geo_subcountry'] for i in geostring.results])
            all_locs.append([i['geo_country'] for i in geostring.results])
        # vertical resolution: match within corresponding fields
        for n,i in enumerate(all_locs):
            loc_list = []
            for j in i:
                loc_list.extend(j.split('?'))
            top_locs = collections.Counter(loc_list).most_common()
            top_n = top_locs[0][1]
            resolved_locs = []
            for j in top_locs:
                if j[1] == top_n or n == 0:
                    resolved_locs.append(j[0])
            resolved_locs = '?'.join(resolved_locs)
            if n == 0:
                resolved_location['resolved_city'] = resolved_locs
            elif n == 1:
                resolved_location['resolved_subcountry'] = resolved_locs
            elif n == 2:
                resolved_location['resolved_country'] = resolved_locs
        #horizontal resolution: match across fields
        r_countries = resolved_location['resolved_country'].split('?')
        r_subcountries = resolved_location['resolved_subcountry'].split('?')
        
        r2_subc = []
        for rc in r_countries:
            r2_subc.extend([rl 
                            for rl 
                            in resolved_location['resolved_subcountry'].split('?') 
                            if rl != '' 
                            and rc in geostring.loc_index[re.sub(geostring.re_sub,'',unidecode(rl).lower().strip())][2]])
        resolved_location['resolved_subcountry'] = '?'.join(sorted(list(set(r2_subc))))
        
        r2_city = []
        for rc in r_subcountries:
            r2_city.extend([rl 
                            for rl 
                            in resolved_location['resolved_city'].split('?') 
                            if rl != '' 
                            and rc in geostring.loc_index[re.sub(geostring.re_sub,'',unidecode(rl).lower().strip())][1]])
        resolved_location['resolved_city'] = '?'.join(sorted(list(set(r2_city))))
        
        return resolved_location    
        
def create_loc_index(world_data_fn='world_places.csv',
                     world_nick_fn='world_nicknames.csv',
                     re_sub='[^a-z]'):
    mod_path = os.path.dirname(os.path.abspath(__file__)) + '/'
    world_data=pd.read_csv(mod_path + world_data_fn,
                           keep_default_na=False,
                           header=None).values.tolist()
    city_index = {re.sub(re_sub,'',unidecode(i[0]).lower().strip()):['','',''] for i in world_data}
    subc_index = {re.sub(re_sub,'',unidecode(i[2]).lower().strip()):['','',''] for i in world_data}
    country_index = {re.sub(re_sub,'',unidecode(i[1]).lower().strip()):['','',''] for i in world_data}
    
    for i in world_data:
        city = re.sub(re_sub,'',unidecode(i[0]).lower().strip())
        subc = re.sub(re_sub,'',unidecode(i[2]).lower().strip())
        country = re.sub(re_sub,'',unidecode(i[1]).lower().strip())
        
        city_index[city][0] = i[0].lower()
        city_index[city][1] += "?" + i[2].lower().strip()
        city_index[city][2] += "?" + i[1].lower().strip()
        
        subc_index[subc][0] = ''
        subc_index[subc][1] = i[2].lower()
        subc_index[subc][2] += "?" + i[1].lower().strip()
        
        country_index[country][0] = ''
        country_index[country][1] = ''
        country_index[country][2] = i[1].lower().strip()
           
    loc_index = {}
    loc_index.update(city_index)
    subc_city_matches = (i for i in subc_index if i in city_index)
    for i in subc_city_matches:
        loc_index[i][1] += "?" + subc_index[i][1]
        loc_index[i][2] += "?" + subc_index[i][2]
    subc_city_nonmatches = {i:subc_index[i] for i in subc_index if i not in city_index}
    loc_index.update(subc_city_nonmatches)
    loc_index.update(country_index) 
    del loc_index['']
    
    for i in loc_index:
        if '?' in loc_index[i][1]:
            loc_index[i][1] = '?'.join(sorted(list(set(loc_index[i][1].split('?')))))
        if '?' in loc_index[i][2]:
            loc_index[i][2] = '?'.join(sorted(list(set(loc_index[i][2].split('?')))))
        if len(loc_index[i][1]) > 0 and loc_index[i][1][0] == '?':
            loc_index[i][1] = loc_index[i][1][1:]
        if len(loc_index[i][2]) > 0 and loc_index[i][2][0] == '?':
            loc_index[i][2] = loc_index[i][2][1:]

    loc_index['georgia'] = ['','georgia','georgia?united states']
    # add nickname data
    if world_nick_fn != '':
        nickname_data = pd.read_csv(mod_path + world_nick_fn,
                                    keep_default_na=False,
                                    header=None).values.tolist()
        nickname_index = {re.sub(re_sub,'',unidecode(i[0]).lower().strip()):['','',''] for i in nickname_data}
        for i in nickname_data:
            nick = re.sub(re_sub,'',unidecode(i[0]).lower().strip())
            nickname_index[nick][0] += "?" + i[1].lower().strip()
            nickname_index[nick][1] += "?" + i[3].lower().strip()
            nickname_index[nick][2] += "?" + i[2].lower().strip()
            
        for i in nickname_index:
            for j in range(3):
                if '?' in nickname_index[i][j]:
                    nickname_index[i][j] = '?'.join(sorted(list(set(nickname_index[i][j].split('?')))))
                if len(nickname_index[i][j]) > 1 and nickname_index[i][j][0] == '?':
                    nickname_index[i][j] = nickname_index[i][j][1:]
                    
    loc_index.update(nickname_index)
    print('World index created.')
    return loc_index
        
class Geostring(object):
    loc_index = create_loc_index()
    def __init__(self,geo_input='',re_sub='[^a-z]',delimiters=[',',';','\|','&',' and ','/','\\\\'],loc_index=''):
        self.geo_input = geo_input
        self.re_sub = re_sub
        self.delimiters = delimiters
        self.results = []
        if loc_index == '':
            self.loc_index = Geostring.loc_index
        else:
            self.loc_index = loc_index
        if geo_input != '':
            delimiters = '|'.join(delimiters)
            geo_input = re.sub(delimiters,',',geo_input)
            for s in geo_input.split(','):
                self.results.append(get_geo_info(s,self.re_sub,self.loc_index))
