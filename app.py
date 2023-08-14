
from PIL import Image as pilimg
import io
import numpy as np
import datetime
import os
import cv2
import matplotlib.pyplot as plt
import pydicom
import pydicom._storage_sopclass_uids
from pydicom.dataset import Dataset
from pydicom.uid import ExplicitVRLittleEndian
import traceback
import shutil
import sys

def convert_to_hu(dicom_file):
    bias = dicom_file.RescaleIntercept
    slope = dicom_file.RescaleSlope
    pixel_values = dicom_file.pixel_array
    new_pixel_values = (pixel_values * slope) + bias
    return new_pixel_values


def reorder_list(el):
    el = os.path.splitext(el)[0]
    return int(el.split("_")[-1])


def img_to_dicom_frames_NormalCompression_NewDicom(folder_path, dest_path, dicom_name, img_format):
    # use pydicom.uid.RLELossless compression
    # microdicom can not read
    try:
        final_result = {"exit_code": 0, "message": ""}
        pixel_data_list = []
        if os.path.exists(folder_path):
            img_list = os.listdir(folder_path)
            img_list.sort(key=reorder_list)
        else:
            final_result["exit_code"] = 1
            final_result["message"] = "folder path not exist!"
            return final_result

        # img to array
        for img_name in img_list:
            img_path = f"{folder_path}/{img_name}"
            img = pilimg.open(img_path)
            np_image = np.array(img.getdata(), dtype=np.uint8)[:, :3]
            np_image = np_image.tobytes() if img_format == "png" else np_image
            pixel_data_list.append(np_image)

        frames_count = len(pixel_data_list)

        # Populate required values for file meta information
        meta = pydicom.Dataset()
        meta.MediaStorageSOPClassUID = pydicom._storage_sopclass_uids.MRImageStorage
        meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

        ds = Dataset()
        ds.file_meta = meta

        ds.is_little_endian = True
        ds.is_implicit_VR = False

        ds.SOPClassUID = pydicom._storage_sopclass_uids.MRImageStorage
        ds.PatientName = "Test^Firstname"
        ds.PatientID = "123456"

        ds.Modality = "MR"
        ds.SeriesInstanceUID = pydicom.uid.generate_uid()
        ds.StudyInstanceUID = pydicom.uid.generate_uid()
        ds.FrameOfReferenceUID = pydicom.uid.generate_uid()

        ds.BitsStored = 8
        ds.BitsAllocated = 8
        ds.SamplesPerPixel = 3
        ds.HighBit = 7

        ds.ImagesInAcquisition = "1"

        ds.Rows = img.height
        ds.Columns = img.width
        ds.InstanceNumber = 1

        ds.ImagePositionPatient = r"0\0\1"
        ds.ImageOrientationPatient = r"1\0\0\0\-1\0"
        ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"

        ds.RescaleIntercept = "0"
        ds.RescaleSlope = "1"
        ds.PixelSpacing = r"1\1"
        ds.PhotometricInterpretation = "RGB"
        ds.PixelRepresentation = 0

        ds.NumberOfFrames = frames_count

        ds.StudyDate = datetime.datetime.now().strftime('%Y%m%d')
        ds.StudyTime = datetime.datetime.now().strftime('%H%M%S')
        ds.ContentDate = datetime.datetime.now().strftime('%Y%m%d')
        ds.ContentTime = datetime.datetime.now().strftime('%H%M%S')

        pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
        pixel_data = b"".join(pixel_data_list)
        ds.PixelData = pixel_data + b"\x00" if len(pixel_data) % 2 else pixel_data
        ds.compress(pydicom.uid.RLELossless, encoding_plugin='pylibjpeg')
        ds.save_as(f"{dest_path}/{dicom_name}")
        print("save dcm end")

        return {"exit_code": 0, "message": f"successfully"}
    except Exception as e:
        return {"exit_code": 1, "message": f"{e}"}


def img_to_dicom_frames_compression_rewrite(dcm_path, img_folder_path):

    path_split = os.path.split(dcm_path)
    filename = path_split[1]
    img_basename = os.path.splitext(filename)[0]
    dest_folder_path = f"{path_split[0]}/{img_basename}_dcm/"
    dest_path = f"{path_split[0]}/{img_basename}_dcm/{filename}"
    
    if os.path.exists(dest_folder_path):
        shutil.rmtree(dest_folder_path, ignore_errors=True)
    os.makedirs(dest_folder_path)

    final_result = {"valid": True, "message": "", "dicom_path": dest_path}
    pixel_data_list = []
    if os.path.exists(img_folder_path):
        img_list = os.listdir(img_folder_path)
        img_list.sort(key=reorder_list)
    else:
        final_result["valid"] = False
        final_result["message"] = "folder path not exist!"
        return final_result

    # img to array
    for img_name in img_list:
        img_path = f"{img_folder_path}/{img_name}"
        img = pilimg.open(img_path)
        image = np.array(img)
        image = pilimg.fromarray(image)
        with io.BytesIO() as output:
            image.save(output, format="JPEG")
            pixel_data_list.append(output.getvalue())
    frames_count = len(pixel_data_list)
    # Populate required values for file meta information
    try:
        ds = pydicom.dcmread(dcm_path)
    except:
        try:    
            ds = pydicom.dcmread(dcm_path, force=True)
        except Exception as e:
            final_result["message"] = traceback.format_exc()
            final_result["valid"] = False
            return final_result
        
    meta = pydicom.Dataset()
    meta.MediaStorageSOPClassUID = pydicom._storage_sopclass_uids.MRImageStorage
    meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    meta.TransferSyntaxUID = "1.2.840.10008.1.2.4.50"

    ds.file_meta = meta

    ds.SOPClassUID = pydicom._storage_sopclass_uids.MRImageStorage
    ds.PatientName = "Test^Firstname"
    ds.PatientID = "123456"

    ds.Modality = "MR"
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.FrameOfReferenceUID = pydicom.uid.generate_uid()

    ds.BitsStored = 8
    ds.BitsAllocated = 8
    ds.SamplesPerPixel = 3
    ds.HighBit = 7

    ds.Rows = img.height
    ds.Columns = img.width
    ds.InstanceNumber = 1

    ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"

    ds.PhotometricInterpretation = "YBR_FULL_422"
    ds.PixelRepresentation = 0

    pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
    ds.PixelData = pydicom.encaps.encapsulate(pixel_data_list)
    ds['PixelData'].is_undefined_length = True

    ds.save_as(dest_path, write_like_original=False)
    return final_result


def img_to_dicom_frames_NormalCompression_rewrite(dicom_path, folder_path):
    final_result = {"exit_code": 0, "message": ""}
    pixel_data_list = []
    if os.path.exists(folder_path):
        img_list = os.listdir(folder_path)
        img_list.sort(key=reorder_list)
    else:
        final_result["exit_code"] = 1
        final_result["message"] = "folder path not exist!"
        return final_result

    # img to array
    # img to array
    for img_name in img_list:
        img_path = f"{folder_path}/{img_name}"
        img = pilimg.open(img_path)
        np_image = np.array(img.getdata(), dtype=np.uint8)[:, :3]
        np_image = np_image.tobytes()
        pixel_data_list.append(np_image)
    frames_count = len(pixel_data_list)
    # Populate required values for file meta information
    meta = pydicom.Dataset()
    meta.MediaStorageSOPClassUID = pydicom._storage_sopclass_uids.MRImageStorage
    meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    ds = pydicom.dcmread(dicom_path)
    ds.file_meta = meta

    ds.is_little_endian = True
    ds.is_implicit_VR = False

    ds.SOPClassUID = pydicom._storage_sopclass_uids.MRImageStorage
    ds.PatientName = "Test^Firstname"
    ds.PatientID = "123456"

    ds.Modality = "MR"
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.FrameOfReferenceUID = pydicom.uid.generate_uid()

    ds.BitsStored = 8
    ds.BitsAllocated = 8
    ds.SamplesPerPixel = 3
    ds.HighBit = 7

    ds.ImagesInAcquisition = "1"

    ds.Rows = img.height
    ds.Columns = img.width
    ds.InstanceNumber = 1

    ds.ImagePositionPatient = r"0\0\1"
    ds.ImageOrientationPatient = r"1\0\0\0\-1\0"
    ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"

    ds.RescaleIntercept = "0"
    ds.RescaleSlope = "1"
    ds.PixelSpacing = r"1\1"
    ds.PhotometricInterpretation = "RGB"
    ds.PixelRepresentation = 0

    pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
    pixel_data = b"".join(pixel_data_list)
    ds.PixelData = pixel_data + b"\x00" if len(pixel_data) % 2 else pixel_data
    ds.compress(pydicom.uid.RLELossless)
    ds.save_as("/home/user/test_data/test_dcms/out/need_fit/jpeg_dicom2.dcm")
    print("save dcm end")


def dcm_to_img_convert(ds, dest_folder_path, img_basename, pixelData, dcm_path, i=0):
    photometric = ds.PhotometricInterpretation
    string = ""
    dpi = 100
    fig, ax = plt.subplots()
    if "YBR" in photometric :
        try:
            pixelData = cv2.cvtColor(pixelData, cv2.COLOR_YUV2RGB)
            ax.imshow(pixelData)
            ax.axis("off")
            ax.margins(0, 0)
            fig.set_size_inches(ds.Columns / 76.99, ds.Rows / 76.99)
            fig.savefig(f"{dest_folder_path}/{img_basename}_{i}.jpg", bbox_inches='tight', pad_inches=0, dpi=dpi)
            plt.close(fig)
        except Exception as e:
            string = f"{i} {photometric} format converter failed! {traceback.format_exc()}"
    elif photometric in ["MONOCHROME1", "MONOCHROME2", '']:
        try:
            level = ds.WindowCenter
            window = ds.WindowWidth
            pixelData = convert_to_hu(ds)
            if len(pixelData.shape) == 3:
                pixelData = pixelData[0]
            try:
                len(window)
                vmin = level[0] - window[0] / 2
                vmax = level[0] + window[0] / 2
            except TypeError:
                vmin = level - window / 2
                vmax = level + window / 2

            if photometric == 'MONOCHROME1':
                ax.imshow(pixelData, cmap=plt.cm.gray_r, vmin=vmin, vmax=vmax)
            else:
                ax.imshow(pixelData, cmap=plt.cm.gray, vmin=vmin, vmax=vmax)
            ax.axis("off")
            ax.margins(0, 0)
            fig.set_size_inches(ds.Columns / 76.99, ds.Rows / 76.99)
            fig.savefig(f"{dest_folder_path}/{img_basename}_{i}.jpg", bbox_inches='tight', pad_inches=0, dpi=dpi)
            plt.close(fig)
        except Exception as e:
            string = f"{i} {photometric} format converter failed! {traceback.format_exc()}"
            try:
                pixelData = ds.pixel_array
                if len(pixelData.shape) == 3:
                    pixelData = pixelData[0]
                if photometric == 'MONOCHROME1':
                    ax.imshow(pixelData, cmap=plt.cm.gray_r)
                else:
                    ax.imshow(pixelData, cmap=plt.cm.gray)
                ax.axis("off")
                ax.margins(0, 0)
                fig.set_size_inches(ds.Columns / 76.99, ds.Rows / 76.99)
                fig.savefig(f"{dest_folder_path}/{img_basename}_{i}.jpg", bbox_inches='tight', pad_inches=0,
                            dpi=dpi)
                plt.close(fig)
            except Exception as e:
                string = f'unknown MONOCHROME format {traceback.format_exc()}'
    elif photometric == "PALETTE COLOR":
        try:
            rgb = pydicom.pixel_data_handlers.util.apply_color_lut(pixelData, ds)
            if len(rgb.shape) == 3:
                ax.imshow(rgb)
                ax.axis("off")
                ax.margins(0, 0)
                fig.set_size_inches(ds.Columns / 76.99, ds.Rows / 76.99)
                fig.savefig(f"{dest_folder_path}/{img_basename}_{i}.jpg", bbox_inches='tight', pad_inches=0, dpi=dpi)
            elif len(rgb.shape) == 4:
                ax.imshow(rgb[0])
                ax.axis("off")
                ax.margins(0, 0)
                fig.set_size_inches(ds.Columns / 76.99, ds.Rows / 76.99)
                fig.savefig(f"{dest_folder_path}/{img_basename}_{i}.jpg", bbox_inches='tight', pad_inches=0, dpi=dpi)
                plt.close(fig)
            else:
                string = 'Shape error! Unknown PALETTE COLOR format'
        except Exception as e:
            string = f"{photometric} format converter failed! {traceback.format_exc()}"
    elif photometric == "RGB":
        try:

            ax.imshow(pixelData)
            ax.axis("off")
            ax.margins(0, 0)
            fig.set_size_inches(ds.Columns / 76.99, ds.Rows / 76.99)
            fig.savefig(f"{dest_folder_path}/{img_basename}_{i}.jpg", bbox_inches='tight', pad_inches=0, dpi=dpi)
            plt.close(fig)
        except Exception as e:
            string = f"{photometric} format converter failed! {traceback.format_exc()}"

    else:
        string = f"{photometric} format not support!"

    valid = True if len(string) == 0 else False
    return {"valid": valid, "message": string}


def dcm_to_img(dcm_path):
    try:
        ds = pydicom.dcmread(dcm_path)
    except:
        try:    
            ds = pydicom.dcmread(dcm_path, force=True)
        except Exception as e:
            result = traceback.format_exc()
            return {"valid": False, "message": f"{result}", "folder_path": ""}

    path_split = os.path.split(dcm_path)
    filename = path_split[1]
    img_basename = os.path.splitext(filename)[0]
    dest_folder_path = f"{path_split[0]}/{img_basename}_jpg"

    final_result = {"valid": True, "message": "", "folder_path": dest_folder_path}
    if os.path.exists(dest_folder_path):
        shutil.rmtree(dest_folder_path, ignore_errors=True)
    os.makedirs(dest_folder_path)

    try:
        shape = ds.pixel_array.shape
        number_of_frame = ds[0x28, 0x08].value
        multi_frames = True
        assert number_of_frame == shape[0]
    except KeyError:
        multi_frames = False
    except Exception as e:
        final_result["valid"] = False
        final_result["message"] = f"{traceback.format_exc()}"
        return final_result
    print("shape", shape)
    if multi_frames:
        for i in range(number_of_frame):
            result = dcm_to_img_convert(ds, dest_folder_path, img_basename, ds.pixel_array[i], dcm_path, i)
            if not result["valid"]:
                final_result["valid"] = False
                final_result["message"] = f"{result['message']}"
                break
    else:
        result = dcm_to_img_convert(ds, dest_folder_path, img_basename, ds.pixel_array, dcm_path)
        if not result["valid"]:
            final_result["valid"] = False
            final_result["message"] = f"{result['message']}"
    return final_result



def show_dicom_tag(dcm_path):
    try:
        result = pydicom.dcmread(dcm_path)
    except:
        try:    
            result = pydicom.dcmread(dcm_path, force=True)
        except Exception as e:
            result = traceback.format_exc()
    return result


def main(mode, dcm_path, img_folder_path):
    # mode: 
    # show_tag: show dicom tag 
    print("start ------------------", mode, dcm_path, img_folder_path)
    start_time = datetime.datetime.now()
    if mode == "show_tag":
        result = show_dicom_tag(dcm_path)
    elif mode == "dcm_2_jpg":
        result = dcm_to_img(dcm_path)
    elif mode == "jpg_2_dcm":
        if not img_folder_path:
            return "img_folder_path can not None"
        result = img_to_dicom_frames_compression_rewrite(dcm_path, img_folder_path)
    elif mode == "convert_all": 
        result = dcm_to_img(dcm_path)
        if result["folder_path"]:
            result = img_to_dicom_frames_compression_rewrite(dcm_path, result["folder_path"])
    else:
        return "mode error"
    end_time = datetime.datetime.now()
    print(f"end ------------------ execution time: {end_time - start_time}")

    return result

if __name__ == "__main__":
    arguments = sys.argv
    if len(arguments) > 1:
        mode = arguments[1]
        dcm_path = arguments[2]
        img_folder_path = arguments[3] if len(arguments) > 3 else None
        print(main(mode, dcm_path, img_folder_path))
    else:
        print("\n arg: \n"\
                "   mode: show_tag, dcm_2_jpg, jpg_2_dcm, convert_all \n"\
                "   dcm_path: dicom file path \n"\
                "   img_folder_path: if mode = jpg_2_dcm, add arg img_folder_path \n")