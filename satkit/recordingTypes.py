
class Recording:
    """
    Superclass for all recording classes.
    """

    def __init__(self):
        self.data = {}
        self.meta = {}
        

class Ultrasound_Recording(Recording):
    """
    Superclass for ultrasound recording classes.
    """

    def __init__(self):
        super.__init__()
    

class AAA_Ult_Recording(Ultrasound_Recording):
    """
    Ultrasound recording exported from AAA.
    """

    def __init__(self, filename = None):
        super.__init__()
        self.parse_promptfile(filename)
        

    def parse_promptfile(self, filename):
    """
    Read an AAA .txt (not US.txt) file and save prompt, recording date and time,  
    and participant name into the meta dictionary.
    """
    with closing(open(filename, 'r')) as promptfile:
        lines = promptfile.read().splitlines()
        self.meta['prompt'] = lines[0]
        self.meta['date'] = lines[1]
        # could also do datetime as below, but there doesn't seem to be any reason to so.
        # date = datetime.strptime(lines[1], '%d/%m/%Y %H:%M:%S')
        self.meta['participant'] = lines[2].split(',')[0]

        _AAA_logger.debug("Read prompt file " + filename + ".")
        

    def parse_ult_meta(self, filename):
    """
    Parse metadata from an AAA 'US.txt' file into the meta dictionary.
    """
    with closing(open(filename, 'r')) as metafile:
        for line in metafile:
            (key, value_str) = line.split("=")
            try:
                value = int(value_str)
            except ValueError:
                value = float(value_str)
            self.meta[key] = value

        _AAA_logger.debug("Read and parsed ultrasound metafile " + filename + ".")


