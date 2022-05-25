from configparser import ConfigParser
import csv

dict_db = {}
config = ConfigParser()
config.read(open(r'scenarios/public_transport_base/scenario.cfg'))
for sect in config.sections():
   print('Section:', sect)
   for k,v in config.items(sect):
      print(' {} = {}'.format(k,v))
   print()


def wrapper():
#    input_file = csv.DictReader(open("scenarios/public_transport_base/schedule.csv"))
#        for row in input_file
#    print row




#schedule = open('.src/scenario_wrapper/schedule.csv', 'w')