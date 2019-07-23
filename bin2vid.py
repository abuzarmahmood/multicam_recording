# ___                            _     __  __           _       _           
#|_ _|_ __ ___  _ __   ___  _ __| |_  |  \/  | ___   __| |_   _| | ___  ___ 
# | || '_ ` _ \| '_ \ / _ \| '__| __| | |\/| |/ _ \ / _` | | | | |/ _ \/ __|
# | || | | | | | |_) | (_) | |  | |_  | |  | | (_) | (_| | |_| | |  __/\__ \
#|___|_| |_| |_| .__/ \___/|_|   \__| |_|  |_|\___/ \__,_|\__,_|_|\___||___/
#              |_|                                                          

import os
import numpy as np
import tqdm
import glob
import cv2
import multiprocessing as mp
import itertools

# _____                 _   _                 
#|  ___|   _ _ __   ___| |_(_) ___  _ __  ___ 
#| |_ | | | | '_ \ / __| __| |/ _ \| '_ \/ __|
#|  _|| |_| | | | | (__| |_| | (_) | | | \__ \
#|_|   \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
                                             

# Finds list of available binary files
def list_binary_files(directory):
    """
    directory :: params :: path to directory containing binary files
    """
    file_list = [os.path.basename(x) for x in glob.glob(directory + '/*.npy')]
    cam_list = [int(file[file.find('cam')+3]) for file in file_list]
    return list(zip(file_list,cam_list))


# Find number of unique cameras from file-names
def unique_cams(directory):
    """
    directory :: params :: path to directory containing binary files
    """
    out_list = list_binary_files(directory)
    return len(np.unique([x[1] for x in out_list]))

# Find name and date of experiment from files
def get_name(directory):
    out_list = list_binary_files(directory)
    return out_list[0][0][:out_list[0][0].find('cam')-1]

# Convert binary files to archive (Get compressed more than images)
def compress_7z(directory):
    os.system("7za a {0}/{1}_archive.7z {2}/*".format(
        os.dirname(directory),
        get_name(directory),
        directory))

def bin2img(input_file_list, output_file_list):
    assert len(input_file_list) == len(output_file_list), "Input list and output list are unequal"
    retval_list = []
    for file_num in tqdm.trange(len(input_file_list)):
        temp_img = np.load(input_file_list[file_num])
        retval = cv2.imwrite(output_file_list[file_num], temp_img)
        retval_list.append(retval)
    return retval_list

# Load binary images into hdf5
def bin2img_execute(directory):
    """
    directory :: params :: path to directory containing binary files
    """
    cam_num = unique_cams(directory)
    file_list = list_binary_files(directory)
    total_frames = len(file_list)

    for cam in range(cam_num):
        img_dir = os.path.dirname(directory) + '/images/cam{0}'.format(cam)
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
   
    input_file_list = [directory + '/' +  file[0] for file in file_list]
    output_file_list = [os.path.dirname(directory) + \
                        '/images/cam{0}'.format(file[1]) + \
                        '/' + file[0].split('.')[0] + '.ppm' for file in file_list]
    
    def chunks(l, n):
        return [l[i:i + n] for i in range(0, len(l), n)]

    n_cpu =  mp.cpu_count()
    input_list_of_lists = chunks(input_file_list, int(len(input_file_list)/n_cpu)) 
    output_list_of_lists = chunks(output_file_list, int(len(output_file_list)/n_cpu)) 

    if len(file_list) > 0:
        pool = mp.Pool(processes = n_cpu)
        results = [pool.apply_async(bin2img, 
            args = (input_list, output_list)) \
                    for (input_list, output_list) in \
                    zip(input_list_of_lists, output_list_of_lists)]
        ret_list = [p.get() for p in results]
        ret_list = list(itertools.chain.from_iterable(ret_list)) 

    else:
       print('No files found')

    print('{0} / {1} images successfully converted'.\
            format(sum(ret_list),total_frames))

def img2vid(directory,
            frame_rate,
            resolution):
    #with open('convert_file.sh','w') as file:
    cam_num = unique_cams(directory)
    basename = get_name(directory)

    for cam in range(cam_num):
        cmd = str("ffmpeg -f image2 -r {0} -s {1}x{2} " 
                "-i {3}_cam{4}_%06d.ppm -b:v {5} {6} \n".format(
                        frame_rate,
                        resolution[0],
                        resolution[1],
                        os.path.dirname(directory) + '/images/cam{}/'.format(cam)\
                        + basename,
                        cam,
                        '10000k',
                        basename + '_cam' + str(cam) + '.avi'
                        ))
            #file.write(cmd)
        exit_flag = os.system(cmd)
        print('Exit flag : {}'.format(exit_flag))
