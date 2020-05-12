
class Recording:
    """
    Superclass for all recording classes.
    """

    def __init__(self):
        self.data = []


class Ultrasound_Recording(Recording):
    """
    Superclass for ultrasound recording classes.
    """


class AAA_Ult_Recording(Ultrasound_Recording):
    """
    Ultrasound recording exported by AAA.
    """
