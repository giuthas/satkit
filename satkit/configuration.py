import sys
from contextlib import closing
from pathlib import Path
from typing import Union

from strictyaml import Bool, Float, Int, Map, Str, YAMLError, load

config = {}

# This is where we store the metadata needed to write out the configuration and
# possibly not mess up the comments in it.
_raw_config_dict = {}

def load_config(filepath: Union[Path, str, None]=None) -> None:
    """
    Read the config file from filepath.
    
    If filepath is None, read from the default file
    'configuration/configuration.yaml'. In both cases if the file does not
    exist, report this and exit.
    """
    if filepath is None:
        filepath = Path('configuration/configuration.yaml')
    elif isinstance(filepath, str):
        filepath = Path(filepath)

    global config
    global _raw_config_dict

    if filepath.is_file():
        with closing(open(filepath, 'r')) as yaml_file:
            schema = Map({
                "satkit constants": Map({
                    "epsilon": Float(),
                    "data/tier height ratios": Map({
                        "data": Int(), 
                        "tier": Int()
                        }),
                    "data run parameters": Str()
                    }),
                "data properties": Map({
                    "data source": Str(), 
                    "speaker id": Str(), 
                    "data directory": Str(), 
                    "outputfilename": Str(),
                    "exclusion list": Str(), 
                    "pronunciation dictionary": Str()
                    }), 
                "flags": Map({
                    "detect beep": Bool(),
                    "only words": Bool(),
                    "test": Bool(),
                    "file": Bool(),
                    "utterance": Bool()
                    })
                })
            try:
                _raw_config_dict = load(yaml_file.read(), schema)
            except YAMLError as error:
                print(f"Fatal error in reading {filepath}:")
                print(error)
                sys.exit()
    else:
        print(f"Didn't find {filepath}. Exiting.".format(str(filepath)))
        sys.exit()
    config.update(_raw_config_dict.data)
