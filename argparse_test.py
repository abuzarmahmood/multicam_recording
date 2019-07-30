import argparse

parser = argparse.ArgumentParser(description = 'Collects names of files to process')
parser.add_argument('marker_file', help = 'File containing start and end times of file')
parser.add_argument('triallist_file', help = 'File containing timestamp of each trial')
parser.add_argument('video_file', help = 'All video files to process', nargs = '+')
args = parser.parse_args()

print('\n')
print('Marker file : {}'.format(args.marker_file))
print('Trial list file: {}'.format(args.triallist_file))
print('Video files : {}'.format(args.video_file))
