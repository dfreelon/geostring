# geostring
**From free-form text to standardized geographical info.**

```geostring``` is a Python module that extracts standardized geographical information from free-form text. It attempts to provide this information at up to three levels of location granularity based on its input: city, subcountry (e.g. state or province), and country. For example, the input "chapel hill" yields the output:

```{"resolved_city":"chapel hill","resolved_subcountry":"north carolina","resolved_country":"united states"}```

Before using ```geostring```, you should understand a few basic facts about how it works:

- First, it performs **fuzzy dictionary matching of unstructured text to known geographic locations**. Upon execution, it seeks the best match for its input string within a built-in database of place names. Match quality is measured using a metric I call tolerance (technically the normalized edit distance/Levenshtein distance). A tolerance of 0 indicates an exact match, while a tolerance of 1 indicates that two strings have no characters in common. So lower is better. The default tolerance threshold is <0.25, which represents the difference between two four-character strings that differ by one letter, such as "lime" and "Lima." It can also be run in "exact" mode, in which it will only retrieve exact string matches between the input text and the database. (This moves several orders of magnitude faster than the fuzzy matching.)
- Second, **tolerance allows you to decide how good your matches have to be.** Setting a low tolerance threshold means all your matches will probably be right, but you may be missing some that didn't make the cut (Type II error). A high tolerance threshold is more permissive, letting through more false positives (Type I error). You may need to adjust based on the nature of your data.
- Third, **when a string could refer to multiple locations, ```geostring``` returns all possible location candidates.** For example, since there are towns named "Oxford" in Alabama, Mississippi, Ohio, and England, its results for "Oxford" are:

	```{'resolved_city':'oxford', 'resolved_subcountry':'alabama?england?mississippi?ohio', 'resolved_country':'united kingdom?united states'}```

	But it can disambiguate multiple candidate locations if provided with additional information. For example, here's the output for "Oxford, USA":

	```{'resolved_city':'oxford', 'resolved_subcountry':'alabama?mississippi?ohio', 'resolved_country':'united states'}```
	
	Because "USA" is present in the input string, ```geostring``` knows the location can't be in England or anywhere else in the UK, so it removes those candidates. For the string "Oxford, UK," the output would be:
	
	```{'resolved_city':'oxford', 'resolved_subcountry':'england', 'resolved_country':'united kingdom'}```

	The "UK" qualifier eliminates all the US towns and returns the sole remaining location matching all the provided criteria.

System requirements
-------------------
- Python 3
- [editdistance](https://github.com/aflc/editdistance)
- [pandas](https://pandas.pydata.org/)
- [unidecode](https://pypi.org/project/Unidecode/)

Installation
------------
```python
pip install geostring
```
Sample code
-----------
```geostring``` has two main user-facing functions: ```resolve``` and ```Geostring``` (which is actually an object class, but it works like a function). Most people will probably only want to use the former, but the latter can be helpful for fine-tuning and troubleshooting. Here are a few sample statements for ```resolve```:
```python
import geostring as geo
#cities, including (some) nicknames
print(geo.resolve('nyc'))
print(geo.resolve('omaha'))
print(geo.resolve('brussels'))
#subcountries
print(geo.resolve('north carolina'))
print(geo.resolve('baja california'))
print(geo.resolve('queensland'))
#countries
print(geo.resolve('kenya'))
print(geo.resolve('mongolia'))
print(geo.resolve('paraguay'))
#fictional places don't work too well
print(geo.resolve('wakanda'))
print(geo.resolve('westeros'))
print(geo.resolve('narnia')) #but some will return false positives based on similarity to real place names!
print(geo.resolve('narnia',exact=True)) #to force an exact string match and reduce false positives
#compound locations
print(geo.resolve('springfield, oh'))
print(geo.resolve('athens, greece'))
print(geo.resolve('san juan, pr'))
#and non-standard location references...
print(geo.resolve('Brooklyn, baby!'))
print(geo.resolve('VA/MD'))
print(geo.resolve('southern California...')) #doesn't work--see below
```
Delimiters
----------------------
Probably the most important determinant of ```geostring```'s performance is the set of characters it treats as delimiters. Every substring separated by a delimiter will be matched separately to the place name database. For example, running
```python 
geo.resolve('southern California...')
``` 
with the default delimiters, which include commas but not spaces, will interpret "southern California" as a single location and thus exceed the tolerance threshold. But if you set ```Geostring``` to use spaces as delimiters like so: 
```python 
geo.resolve('southern California...',delimiters=[' '])
```
it will look up "southern" and "California" separately, drop "southern" because it exceeds the threshold, and match only "California." You may want to set up rules governing which delimiters ```geostring``` uses based on the characteristics of each string in your dataset. For example you might choose to use spaces as delimiters only with strings that end in two- or three-letter sequences, e.g. "Cincinnati OH" or "Cape Town ZA". 

The default delimiters are commas, semicolons, pipes, ampersands, the word "and" surrounded by a space on each side, forward slashes, and backslashes (see "Parameters" section below). 

Function and object details
-----------------

**Input**

```Geostring``` objects take strings as input, and ```resolve``` takes ```Geostring``` objects as input. Because these functions try to match all substrings generated by splitting on the chosen delimiters, they work best on data from dedicated location fields (such as Twitter's). ```geostring``` probably won't work as well on text not specifically devoted to location info--in particular, it will misinterpret certain short words as country codes (e.g. "to"->Tonga, "in"->Indiana, "me"->Maine, etc.)

**Parameters**

Aside from its input, ```Geostring``` objects possess the following parameters:
- ```re_sub```: The regex pattern used to preprocess the input string. By default it is ```[^a-z]``` which removes all non-Latin letter characters, including spaces.
- ```delimiters```: A list containing the delimiters used to preprocess the input string. By default it is ```[',',';','\|','&',' and ','/','\\\\']```
- ```loc_index```: The location index used to match strings. This is generated automatically when ```geostring``` is imported.
- ```exact```: Boolean; toggles exact string matching mode (and accelerates execution considerably). ```False``` by default.

Aside from its input, ```resolve``` possesses three additional parameters:

- ```exact```: Boolean; toggles exact string matching mode (and accelerates execution considerably). ```False``` by default. Setting this to ```True``` will change ```max_tolerance``` to 0 regardless of what the user has entered for the latter.
- ```max_tolerance```: The upper limit of the tolerance between the input string and its best match in the place name database. If the best match returns a tolerance equaling or exceeding this value, ```resolve``` will return ```None```. 0.25 by default.
- ```verbose```: Boolean; displays additional info about your output. ```False``` by default.

**Output**

```Geostring``` objects have the following attributes:
- ```delimiters```: Reproduces the argument for the ```delimiters``` parameter.
- ```geo_input```: The raw (unpreprocessed) input string.
- ```loc_index```: A dict containing the place name database used to match input strings. Keys are the names of cities, subcountries, and countries. Values are the locations corresponding to the keys (so each value is a three-string list in ```[city, subcountry, country]``` order). Subcountry keys have an empty string in the "city" slot, while country keys have empty strings in the "city" and "subcountry" slots.
- ```re_sub```: Reproduces the argument for the ```re_sub``` parameter.
-  ```results```: An OrderedDict containing the results of the ```Geostring``` operation, including:
   - ```geo_input```: Same as above, included here for convenience.
   - ```geo_input_pp```: The input string after regex preprocessing with ```re_sub```.
   - ```geo_input_match```: The best match from the place name database for ```geo_input_pp```. Good for troubleshooting.
   - ```geo_city```: The city/town name(s) associated with ```geo_input_match```. Multiple matching cities are separated by question marks.
   - ```geo_subcountry```: The subcountry name(s) associated with ```geo_input_match```. Multiple matching subcountries are separated by question marks.
   - ```geo_country```: The country name(s) associated with ```geo_input_match```. Multiple matching countries are separated by question marks.
   - ```ed_best_match```: The edit distance of the match between ```geo_input_pp``` and ```geo_input_match```.
   - ```ed_tolerance```: The tolerance of the best edit distance, which is defined as ```ed_best_match```/```max(len(geo_input_pp),len(geo_input_match))```

```resolve``` produces an OrderedDict containing three items:
- ```resolved_city```: The most likely city name(s) based on the input string.
- ```resolved_subcountry```: The most likely subcountry name(s).
- ```resolved_country```: The most likely country name(s).

About the place name databases
-----------------------------------
```geostring``` combines two location databases into one when it is imported: one contains official place names (```world_places.csv```) and the other contains place nicknames (```world_nicknames.csv```). The official place name database is derived from this one: https://datahub.io/core/world-cities but it is not perfect: for example, I noticed it has very few cities in the US state of Virginia. It probably has other deficiencies I haven't yet noticed. It claims to include all cities with more than 15,000 people but I have not verified that.

Fortunately the two files are very easy to extend. The official name database is a CSV in which the first column is the city, the second column is the country, and the third column is the subcountry. So you can append new locations to the file in that format if you wish. Please note that you should only add the official names of cities and towns to this file.

If you wish to add standalone subcountries, countries, or nicknames for any location, use the nicknames file (```world_nicknames.csv```). For our purposes, a "nickname" is any name other than a place's official or most commonly used name (like place name abbreviations). This file is organized differently: the nickname goes in the first column, then the city, then country, then subcountry. If there is no corresponding city or subcountry, simply leave the cell blank. The file currently includes all two-letter US state abbreviations, all two-letter Canadian province abbreviations, all two- and three-letter country abbreviations, and a bunch of common place nicknames I added manually at the end. You can add whatever nicknames or abbreviations you like as long as you stick to the format.

Non-Latin characters
---------------------------
```geostring``` uses the ```unidecode``` module to ASCII-ize non-Latin characters. For example, ```geo.resolve('Zürich')``` automatically replaces the "ü" with a "u" to ensure a perfect match with "Zurich." ```unidecode``` provides limited support for non-Latin place names, although the quality of the conversion varies based on the character set. ```geo.resolve('北京')``` gives a perfect match for "Beijing," while ```geo.resolve('서울')``` does the same for "Seoul." But other character sets don't work as well: Arabic and Greek generally perform poorly, while Russian fares variably (compare ```geo.resolve('Владивосток')``` to ```geo.resolve('Москва')```.)
