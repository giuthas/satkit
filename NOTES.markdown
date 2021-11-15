
Qt version of UI:

As detailed here
https://stackoverflow.com/questions/60828957/adding-more-than-one-property-to-a-gui-built-with-qt-designer-causes-systemerror
the SATKIT Qt user interface needs a PyQt version of 5.13 or above. In
Nov 2021 anaconda was still stuck in 5.9, so this was run to install a
better version: pip install PyQt5. This apparently messes with the
spyder IDE, which relies on PyQt below 5.13.
