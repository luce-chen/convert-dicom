# convert-dicom
dicom to jpg or jpg to dicom

## environment
python3.6 or latester, pydicom2.3.1, cv2, matplotlib


## arg

### mode: show_tag, convert_img, convert_dcm, convert_all 
show_tag: show dicom all tag
dcm_2_jpg: single/multiple-frames dicom to jpg images
jpg_2_dcm: jpg images to single/multiple-frames dicom (need dcm file as base)
convert_all: dicom to jpg and jpg to dicom

### dcm_path: dicom file path

### img_folder_path: if mode = jpg_2_dcm, add arg img_folder_path

## example
python app.py "show_tag" "test.dcm"
python app.py "jpg_2_dcm" "test.dcm" "jpg_folder"
