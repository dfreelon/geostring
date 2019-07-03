from setuptools import setup
setup(
  name = 'geostring',
  packages = ['geostring'], # this must be the same as the name above
  version = '1.0.7',
  description = 'geostring',
  author = 'Deen Freelon',
  author_email = 'dfreelon@gmail.com',
  url = 'https://github.com/dfreelon/geostring/', # use the URL to the github repo
  download_url = 'https://github.com/dfreelon/geostring/', 
  install_requires = ['editdistance','pandas','unidecode'],
  keywords = ['geographic', 'location', 'places', 'geolocation'], # arbitrary keywords
  classifiers = [],
  include_package_data=True
)