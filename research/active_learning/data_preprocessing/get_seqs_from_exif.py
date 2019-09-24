import csv
from datetime import datetime
from dateutil.parser import parse
import json
import numpy as np
import os
from PIL import Image
from PIL.ExifTags import TAGS
import uuid
import tqdm

# detector_output_path = '/datadrive/SUCP/detector_output.csv'
# detector_output = [row for row in csv.DictReader(open(detector_output_path))]
# image_file = detector_output[0]['image_path']
# img = Image.open(image_file)

img_metadata = {}

def get_PILImage_exif(PILImage):
    img_exif = PILImage._getexif()
    labeled_img_exif = {}
    for (k, v) in img_exif.items():
        labeled_img_exif[TAGS.get(k)] = v
    return labeled_img_exif['DateTimeOriginal']

image_dir = '/datadrive/SUCP/images'
for root, dirs, files in os.walk(image_dir):
    if len(files)>0:
        print(root)
        # Get the datetime objects for when each photo was taken (assumes filenames are already mainly ordered by time)
        unordered_filepaths = [os.path.join(root, f) for f in files if '.JPG' in f]
        unordered_filedatetimes = []
        for fpidx in tqdm.tqdm(range(len(unordered_filepaths))):
            img = Image.open(unordered_filepaths[fpidx])
            datetime_str = get_PILImage_exif(img)
            img_datetime = parse(str(datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S')))
            unordered_filedatetimes.append(img_datetime)
        filedatetimes = sorted(unordered_filedatetimes)
        filepaths = [unordered_filepaths[i[0]] for i in sorted(enumerate(unordered_filedatetimes), key=lambda x:x[1])]

        # Compute differences between successive datetimes
        datetime_diffs = [(filedatetimes[i]-filedatetimes[i-1]).total_seconds() for i in range(1, len(filedatetimes))]

        # Get index for the first frame in each sequence
        new_seq_start_idxs = [0] + [i+1 for i, x in enumerate(datetime_diffs) if x > 2]
        for seq_idx in range(len(new_seq_start_idxs)):
            seq_id = str(uuid.uuid4()) # generate a sequence id
            # get the number of frames
            if seq_idx < len(new_seq_start_idxs) - 1:
                seq_num_frames = new_seq_start_idxs[seq_idx+1] - new_seq_start_idxs[seq_idx]
            else:
                seq_num_frames = len(filepaths) - new_seq_start_idxs[seq_idx]
            for i in range(seq_num_frames):
                fidx = new_seq_start_idxs[seq_idx] + i
                img_metadata[filepaths[fidx]] = {'seq_id': seq_id, 'seq_num_frames': seq_num_frames, 'frame_num': i}
        
with open('/datadrive/SUCP/images_metadata.json', 'w') as outfile:
    json.dump(img_metadata, outfile)
