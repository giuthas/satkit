# Writing a New Modality

We separate data containment, creation (and related import/export/save/load and algorithmic generation), and modification. A new Modality class will be responsible for containing a new type of data, but not for creating itself nor for writing itself to files etc.
