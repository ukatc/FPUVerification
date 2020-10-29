"""
This script in its current configuration script will read in
the file baddatum.txt. and analyse all images in within,
printing the results, once it is done it will print a short
summary. The other files can be used to record names of failed
images, useful to reduce subsequent run times, or to exclude
corrupted images which can not be analysed 

"""
from os import listdir, linesep
from os.path import isfile,join
from shutil import copyfile

import cv2

from ImageAnalysisFuncs import target_detection_otsu as otsu
from ImageAnalysisFuncs.target_detection_otsu import OtsuTargetFindingError
from vfr import conf



listname="baddatum.txt"#="image-list-blob-errors-dat-rep"
outfilename=None#"still-broken-imagesdat"
brokenfilename=None#"wont-opendat"
goodfilename=None#"images-okdat"


in_folder="/moonsdata/verification/images/C0069/datum-repeatability/2020-07-01T09.43.51.940BST/"
out_folder="outdat"
bad_out_folder="stillbaddat"
bad_vis_out_folder="stillbadvisdat"

#onlyimages = [f for f in listdir(in_folder) if isfile(join(in_folder, f))]

good_num = 0
bad_num = 0

tolerence = 7

with open(listname) as listf:
    filelist = listf.read().splitlines()
if outfilename:
    with open(outfilename) as badlist: 
        badfilelist = badlist.read().splitlines()

if brokenfilename:
    with open(brokenfilename) as brokenlist: 
        brokenfilelist = brokenlist.read().splitlines()

if goodfilename:
    with open(goodfilename) as goodlist: 
        goodfilelist = goodlist.read().splitlines()

#with open(outfilename,"a") as outfile, open(goodfilename,"a") as goodoutfile: 
for imagefile in filelist:
    #if (imagefile in badfilelist) or (imagefile in goodfilelist):
    #    continue
    ipath= join(in_folder,imagefile)
    #outname = join(outpath,filename[7:13].replace("/","-") + filename[-39:] )
    #obpath= join(bad_out_folder,image)    
    #ovpath= join(bad_vis_out_folder,image)
    try:
        targets = otsu.find_bright_sharp_circles(ipath,
            small_radius = conf.DAT_REP_TARGET_DETECTION_OTSU_PARS.SMALL_RADIUS/ conf.DAT_REP_PLATESCALE,
            large_radius = conf.DAT_REP_TARGET_DETECTION_OTSU_PARS.LARGE_RADIUS/ conf.DAT_REP_PLATESCALE,
            threshold = 100,#conf.DAT_REP_TARGET_DETECTION_OTSU_PARS.THRESHOLD_LIMIT,
            group_range = conf.DAT_REP_TARGET_DETECTION_OTSU_PARS.GROUP_RANGE/ conf.DAT_REP_PLATESCALE,
            quality = conf.DAT_REP_TARGET_DETECTION_OTSU_PARS.QUALITY_METRIC,
            show=False,
            blob_size_tolerance=conf.DAT_REP_TARGET_DETECTION_OTSU_PARS.BLOB_SIZE_TOLERANCE,
            group_range_tolerance=conf.DAT_REP_TARGET_DETECTION_OTSU_PARS.GROUP_RANGE_TOLERANCE)
    except OtsuTargetFindingError as oe:
        #with open(brokenfilename,"a") as brokenfile: 
            #brokenfile.write(imagefile + linesep)
        print("This ain't working")
        raise oe
    print(imagefile)
    for thing in targets:
        print(thing.pt[0], thing.pt[1], thing.size)
    print(len(targets))
    if len(targets) ==2:
        good_num+=1
        #goodoutfile.write(imagefile + linesep) 
    else:
        bad_num +=1
        #print targets
        #outfile.write(imagefile + linesep) 
        #copyfile(ipath, obpath)
        #cv2.imwrite(ovpath,image)
    #cv2.imwrite(opath,image)

print "Tolerence   : {}".format(tolerence)
print "Good images : {}".format(good_num)
print "Total images: {}".format(good_num+bad_num)
