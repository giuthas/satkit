from pd import *

def main(args):
    directory = args[0]
    
    exclusion_list_name = None
    if len(args) > 1:
        exclusion_list_name = args[1]


    # this is the actual list of tokens that gets processed 
    # including meta data contained outwith the ult file
    token_list = get_token_list_from_dir(directory, exclusion_list_name)

    # run PD on each token
    data = [pd(token) for token in token_list]

    # do something sensible with the data
    draw_spaghetti(token_list, data)
    

if (len(sys.argv) > 2):
    print("\npd.py")
    print("\tusage: python pd.py uti_directory [exclusion_list]")
    print("\n\tReads .ult-files and generates pd plots based of the raw ultrasound data contained in them.")
    print("\n\tUnfinished!")
    sys.exit(0)


if (__name__ == '__main__'):
    t = time.time()
    main(sys.argv[1:])
    print 'Elapsed time', (time.time() - t)
