#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from hermes_python.hermes import Hermes
from hermes_python.ffi.utils import MqttOptions
from hermes_python.ontology import *
import io

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

class SnipsConfigParser(configparser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, configparser.Error) as e:
        return dict()

def subscribe_intent_callback(hermes, intentMessage):
    conf = read_configuration_file(CONFIG_INI)
    action_wrapper(hermes, intentMessage, conf)


def action_wrapper(hermes, intentMessage, conf):
    """ Write the body of the function that will be executed once the intent is recognized. 
    In your scope, you have the following objects : 
    - intentMessage : an object that represents the recognized intent
    - hermes : an object with methods to communicate with the MQTT bus following the hermes protocol. 
    - conf : a dictionary that holds the skills parameters you defined. 
      To access global parameters use conf['global']['parameterName']. For end-user parameters use conf['secret']['parameterName'] 
     
    Refer to the documentation for further details. 
    """
    
    import json
    import os
    
    custom_data = json.loads(intentMessage.custom_data)
    
    if len(intentMessage.slots.password) > 0:
      password = intentMessage.slots.password.first().value  
      if password == conf['secret']['password']:    
        if custom_data['flow'] == "OpenTheDoor":
          result_sentence = "Letting you in!"
          
          text_file = open("/tmp/smart-door-bell-door-state", "w")
          text_file.write("open")
          text_file.close()
    
          os.system("/tmp/matrix-voice-led-control 0 5 0 2000 &")
    
        elif custom_data['flow'] == "SetPassword":
          conf['secret']['password'] = custom_data['password']
          result_sentence = "The password was changed"
          
          conf_parser = SnipsConfigParser()      
          with io.open("config.ini", encoding=CONFIGURATION_ENCODING_FORMAT) as f:
              conf_parser.readfp(f)
          
          conf_parser.set('secret', 'password', custom_data['password'])
          with io.open("config.ini", 'w+', encoding=CONFIGURATION_ENCODING_FORMAT) as f2:
              conf_parser.write(f2)
    
          os.system("/tmp/matrix-voice-led-control 0 5 3 2000 &")
    
      else:
        result_sentence = "Wrong password! Please try again!"
        
        text_file = open("/tmp/smart-door-bell-door-state", "w")
        text_file.write("locked")
        text_file.close()
    
        os.system("/tmp/matrix-voice-led-control 5 0 0 2000 &")
    
    else:
      result_sentence = "Sorry! I need a password."
      
      os.system("/tmp/matrix-voice-led-control 5 0 0 2000 &")
    
    hermes.publish_end_session(intentMessage.session_id, result_sentence)
    


if __name__ == "__main__":
    mqtt_opts = MqttOptions()
    with Hermes(mqtt_options=mqtt_opts) as h:
        h.subscribe_intent("bluetiger9:TellPassword", subscribe_intent_callback) \
         .start()
