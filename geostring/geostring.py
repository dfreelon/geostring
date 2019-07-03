import collections
import editdistance as ed
import os
import pandas as pd
import re
from unidecode import unidecode

filename = __file__
        
def get_geo_info(geo_input='',
                 re_sub='',
                 loc_index=None,
                 exact=False):
    geo_input_pp = re.sub(re_sub,
                          '',
                          unidecode(geo_input).lower().strip())
    curr_match = (None,1000)
    
    if exact == True:
        if geo_input_pp in loc_index:
            curr_match = (geo_input_pp,0)
        else:
            curr_match = (None,1)
    else:
        for i in loc_index:
            ed_match = ed.eval(geo_input_pp,i)
            if ed_match < curr_match[1]:
                curr_match = (i,ed_match)
    if curr_match[0] is not None:
        geodict = collections.OrderedDict(
            {'geo_input':geo_input,
             'geo_input_pp':geo_input_pp,
             'geo_input_match':curr_match[0],
             'geo_city':loc_index[curr_match[0]][0],
             'geo_subcountry':loc_index[curr_match[0]][1],
             'geo_country':loc_index[curr_match[0]][2],
             'ed_best_match':curr_match[1],
             'ed_tolerance':curr_match[1]/max(len(geo_input_pp),
                                              len(curr_match[0]))})
    else:
        geodict = collections.OrderedDict(
            {'geo_input':geo_input,
             'geo_input_pp':geo_input_pp,
             'geo_input_match':None,
             'geo_city':None,
             'geo_subcountry':None,
             'geo_country':None,
             'ed_best_match':curr_match[1],
             'ed_tolerance':1})
    return geodict
    
def resolve(loc_string,
            exact=False,
            max_tolerance=0.25,
            verbose=False):
    if exact == True:
        max_tolerance = 0
    geostr = Geostring(loc_string,exact=exact)
    for i in geostr.results:
        if i['ed_tolerance'] > max_tolerance:
            if verbose == True:
                print('Tolerance between "' + 
                      i['geo_input'] + 
                      '" and "' + 
                      i['geo_input_match'] + 
                      '" (' + 
                      str(i['ed_tolerance']) + 
                      ') equals or exceeds max tolerance of',
                      max_tolerance,
                      '; removing...')
    geostr.results = [i for i 
                         in geostr.results 
                         if i['ed_tolerance'] <= max_tolerance]
                
    if geostr.results == []:
        if verbose == True:
            print('No results, Geostring object empty...')
        return
    else:
        resolved_location = collections.OrderedDict({'resolved_city':'',
                         'resolved_subcountry':'',
                         'resolved_country':''})
        if len(geostr.results) == 1:
            resolved_location['resolved_city'] = geostr.results[0]['geo_city']
            resolved_location['resolved_subcountry'] = geostr.results[0]['geo_subcountry']
            resolved_location['resolved_country'] = geostr.results[0]['geo_country']
            return resolved_location
        else:        
            all_locs = []
            all_locs.append([i['geo_city'] 
                             for i 
                             in geostr.results])
            all_locs.append([i['geo_subcountry'] 
                             for i 
                             in geostr.results])
            all_locs.append([i['geo_country'] 
                             for i 
                             in geostr.results])
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
                            and rc 
                            in geostr.loc_index[
                                         re.sub(
                                            geostr.re_sub,
                                            '',
                                            unidecode(rl).lower().strip())][2]])
        resolved_location['resolved_subcountry'] = '?'.join(sorted(list(set(r2_subc))))
        
        r2_city = []
        for rc in r_subcountries:
            r2_city.extend([rl 
                            for rl 
                            in resolved_location['resolved_city'].split('?') 
                            if rl != '' 
                            and rc in geostr.loc_index[re.sub(geostr.re_sub,
                           '',
                           unidecode(rl).lower().strip())][1]])
        resolved_location['resolved_city'] = '?'.join(sorted(list(set(r2_city))))
        
        return resolved_location    

def get_places(wd,colnum,level,list_out=True):
    if list_out == True:
        return [i 
                for i 
                in wd 
                if any(c == i[colnum] 
                       for c 
                       in level)]
    else:
        return {i:wd[i]
                for i
                in wd
                if any(c 
                       in wd[i][colnum] 
                       for c 
                       in level)}
        
def create_loc_index(world_data_fn='world_places.csv',
                     world_nick_fn='world_nicknames.csv',
                     re_sub='[^a-z]',
                     cities=None,
                     subcountries=None,
                     countries=None):
    mod_path = os.path.dirname(os.path.abspath(filename)) + '/'
    world_data1=pd.read_csv(mod_path + world_data_fn,
                            keep_default_na=False,
                            header=None).values.tolist()
    for n,i in enumerate(world_data1):
        for x,j in enumerate(i):
            world_data1[n][x] = unidecode(j).lower().strip()
            
    world_data = []
    
    if type(countries) is list:
        world_data.extend(
                get_places(
                        world_data1,1,countries))         
    if type(subcountries) is list:
        world_data.extend(
                get_places(
                        world_data1,2,subcountries))
    if type(cities) is list:
        world_data.extend( 
                get_places(
                        world_data1,0,cities))
                           
    if len(world_data) == 0:
        world_data = world_data1
        
    city_index = {re.sub(re_sub,'',i[0]):['','',''] for i in world_data}
    subc_index = {re.sub(re_sub,'',i[2]):['','',''] for i in world_data}
    country_index = {re.sub(re_sub,'',i[1]):['','',''] for i in world_data}
    
    for i in world_data:
        city = re.sub(re_sub,'',i[0])
        subc = re.sub(re_sub,'',i[2])
        country = re.sub(re_sub,'',i[1])
        
        city_index[city][0] = i[0]
        city_index[city][1] += "?" + i[2]
        city_index[city][2] += "?" + i[1]
        
        subc_index[subc][0] = ''
        subc_index[subc][1] = i[2]
        subc_index[subc][2] += "?" + i[1]
        
        country_index[country][0] = ''
        country_index[country][1] = ''
        country_index[country][2] = i[1]
           
    loc_index = {}
    loc_index.update(city_index)
    subc_city_matches = (i for i in subc_index if i in city_index)
    for i in subc_city_matches:
        loc_index[i][1] += "?" + subc_index[i][1]
        loc_index[i][2] += "?" + subc_index[i][2]
    subc_city_nonmatches = {i:subc_index[i] for i in subc_index if i not in city_index}
    loc_index.update(subc_city_nonmatches)
    loc_index.update(country_index)
    if '' in loc_index:
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

    # add nickname data
    if world_nick_fn != '':
        nickname_data1 = pd.read_csv(mod_path + world_nick_fn,
                                     keep_default_na=False,
                                     header=None).values.tolist()
        for n,i in enumerate(nickname_data1):
            for x,j in enumerate(i):
                nickname_data1[n][x] = unidecode(j).lower().strip()
                
        nickname_data = []
    
        if type(countries) is list:
            nickname_data.extend(
                    get_places(
                            nickname_data1,2,countries))         
        if type(subcountries) is list:
            nickname_data.extend(
                    get_places(
                            nickname_data1,3,subcountries))
        if type(cities) is list:
            nickname_data.extend( 
                    get_places(
                            nickname_data1,1,cities))
                               
        if len(nickname_data) == 0:
            nickname_data = nickname_data1
                
        nickname_index = {re.sub(re_sub,'',i[0]):['','',''] 
                          for i in nickname_data}
        for i in nickname_data:
            nick = re.sub(re_sub,'',i[0])
            nickname_index[nick][0] += "?" + i[1]
            nickname_index[nick][1] += "?" + i[3]
            nickname_index[nick][2] += "?" + i[2]
            
        for i in nickname_index:
            for j in range(3):
                if '?' in nickname_index[i][j]:
                    nickname_index[i][j] = '?'.join(sorted(list(set(nickname_index[i][j].split('?')))))
                if len(nickname_index[i][j]) > 1 and nickname_index[i][j][0] == '?':
                    nickname_index[i][j] = nickname_index[i][j][1:]
                    
    loc_index.update(nickname_index)
    print('World index created.')
    return loc_index

def subset_locations(cities=None,
                     subcountries=None,
                     countries=None):
    base_li = create_loc_index(countries=countries,
                               subcountries=subcountries,
                               cities=cities)
    modified_li = {}
    if type(countries) is list:
        modified_li.update(
            get_places(
                base_li,2,countries,False))
    if type(subcountries) is list:
        modified_li.update(
            get_places(
                base_li,1,subcountries,False))
    if type(cities) is list:
        modified_li.update(
            get_places(
                base_li,0,cities,False))

    if len(modified_li) == 0:
        print("No locations entered; location index not modified")
    else:
        Geostring.loc_index = modified_li
        mod_places = [i 
                      for i 
                      in [cities,subcountries,countries]
                      if i is not None]
        print("Location index modified:",mod_places)
      
def restore_locations():
    Geostring.loc_index = create_loc_index()
        
class Geostring(object):
    loc_index = create_loc_index()
    def __init__(self,
                 geo_input='',
                 re_sub='[^a-z]',
                 delimiters=[',',
                             ';',
                             '\|',
                             '&',
                             ' and ',
                             '/',
                             '\\\\'],
                 loc_index='',
                 exact=False):
        self.geo_input = geo_input
        self.re_sub = re_sub
        self.delimiters = delimiters
        self.exact = exact
        self.results = []
        if loc_index == '':
            self.loc_index = Geostring.loc_index
        else:
            self.loc_index = loc_index
        if geo_input != '':
            delimiters = '|'.join(delimiters)
            geo_input = re.sub(delimiters,',',geo_input)
            for s in geo_input.split(','):
                self.results.append(
                        get_geo_info(s,
                                     self.re_sub,
                                     self.loc_index,
                                     self.exact))
