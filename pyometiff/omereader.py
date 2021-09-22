# This file is part of the pyometiff library.

# pyometiff is distributed under the GNU General Public License v3.0 (GNU GPLv3),
# specific files are distributed under different licenses, please refer to the
# file header.

# Modification and redistribution is possible under the terms of the applied 
# license agreement.

# This software is distributed WITHOUT ANY WARRANTY.
# See the GNU General Public License v3.0 for further details.

# A copy of the GNU General Public License v3.0 should be included in pyometiff,
# if you didn't receive a copy, visit <http://www.gnu.org/licenses/>.

# Copyright (c) 2021, Filippo Maria Castelli


from pathlib import Path
import pathlib
from lxml import etree as ET

from pyometiff.omexml import OMEXML

import tifffile
import numpy as np
import logging

class OMETIFFReader:
    def __init__(self,
                 fpath: pathlib.Path,
                 imageseries: int = 0):
        
        self.fpath = Path(fpath)
        self.imageseries = imageseries

    def read(self) -> (np.ndarray, dict, str):
        self.array, self.omexml_string = self._open_tiff(self.fpath)
        self.metadata = self.parse_metadata(self.omexml_string)
        return self.array, self.metadata, self.omexml_string

    def write_xml(self):
        if not hasattr(self, "omexml_string"):
            _, _, _ = self.read()
        xml_fpath = self.fpath.parent.joinpath(self.fpath.stem + ".xml")
        tree = ET.ElementTree(ET.fromstring(self.omexml_string.encode("utf-8")))
        tree.write(str(xml_fpath), encoding="utf-8", method="xml", pretty_print=True)

    def parse_metadata(self, omexml_string):
        if omexml_string is None:
            logging.warning("File {} has no OME-XML tags!".format(str(self.fpath)))
            return None
        self.ox = OMEXML(self.omexml_string)
        metadata = self._get_metadata_template()
        metadata["Directory"] = str(self.fpath.parent)
        metadata["Filename"] = str(self.fpath.name)
        metadata["Extension"] = "ome.tiff"
        metadata["ImageType"] = "ometiff"
        metadata["AcquisitionDate"] = self.ox.image(self.imageseries).AcquisitionDate
        metadata["Name"] = self.ox.image(self.imageseries).Name

        # image dimensions
        metadata["SizeT"] = self.ox.image(self.imageseries).Pixels.SizeT
        metadata["SizeZ"] = self.ox.image(self.imageseries).Pixels.SizeZ
        metadata["SizeC"] = self.ox.image(self.imageseries).Pixels.SizeC
        metadata["SizeX"] = self.ox.image(self.imageseries).Pixels.SizeX
        metadata["SizeY"] = self.ox.image(self.imageseries).Pixels.SizeY

        # physical size
        metadata["PhysicalSizeX"] = self.ox.image(self.imageseries).Pixels.PhysicalSizeX
        metadata["PhysicalSizeY"] = self.ox.image(self.imageseries).Pixels.PhysicalSizeY
        metadata["PhysicalSizeZ"] = self.ox.image(self.imageseries).Pixels.PhysicalSizeZ

        # physical size unit
        metadata["PhysicalSizeXUnit"] = self.ox.image(
            self.imageseries
        ).Pixels.PhysicalSizeXUnit
        metadata["PhysicalSizeYUnit"] = self.ox.image(
            self.imageseries
        ).Pixels.PhysicalSizeYUnit
        metadata["PhysicalSizeZUnit"] = self.ox.image(
            self.imageseries
        ).Pixels.PhysicalSizeZUnit

        # number of image series
        metadata["TotalSeries"] = self.ox.get_image_count()
        metadata["Sizes BF"] = [
            metadata["TotalSeries"],
            metadata["SizeT"],
            metadata["SizeZ"],
            metadata["SizeC"],
            metadata["SizeY"],
            metadata["SizeX"],
        ]

        # get number of image series
        metadata["TotalSeries"] = self.ox.get_image_count()
        metadata["Sizes BF"] = [
            metadata["TotalSeries"],
            metadata["SizeT"],
            metadata["SizeZ"],
            metadata["SizeC"],
            metadata["SizeY"],
            metadata["SizeX"],
        ]

        # get dimension order
        metadata["DimOrder BF"] = self.ox.image(self.imageseries).Pixels.DimensionOrder

        # reverse the order to reflect later the array shape
        metadata["DimOrder BF Array"] = metadata["DimOrder BF"][::-1]

        # DimOrder custom field
        metadata["DimOrder"] = metadata["DimOrder BF Array"]
        
        # get all image IDs
        for i in range(self.ox.get_image_count()):
            metadata["ImageIDs"].append(i)

        # get information about the instrument and objective
        try:
            metadata["InstrumentID"] = self.ox.instrument(self.imageseries).get_ID()
        except (KeyError, AttributeError, IndexError) as e:
            print("Key not found:", e)
            metadata["InstrumentID"] = None
        try:
            metadata["DetectorModel"] = self.ox.instrument(
                self.imageseries
            ).Detector.get_Model()
            metadata["DetectorID"] = self.ox.instrument(
                self.imageseries
            ).Detector.get_ID()
            metadata["DetectorType"] = self.ox.instrument(
                self.imageseries
            ).Detector.get_Type()
        except (KeyError, AttributeError, IndexError) as e:
            print("Key not found:", e)
            metadata["DetectorModel"] = None
            metadata["DetectorID"] = None
            metadata["DetectorType"] = None

        try:
            metadata["MicroscopeType"] = self.ox.instrument(
                self.imageseries
            ).Microscope.get_Type()
        except (KeyError, AttributeError, IndexError) as e:
            print("key not found", e)

        try:
            metadata["ObjNA"] = self.ox.instrument(
                self.imageseries
            ).Objective.get_LensNA()
            metadata["ObjID"] = self.ox.instrument(self.imageseries).Objective.get_ID()
            metadata["ObjMag"] = self.ox.instrument(
                self.imageseries
            ).Objective.get_NominalMagnification()
        except (KeyError, AttributeError, IndexError) as e:
            print("Key not found:", e)
            metadata["ObjNA"] = None
            metadata["ObjID"] = None
            metadata["ObjMag"] = None

        # get channel names
        metadata["Channels"] = self._parse_channels(metadata["SizeC"], self.ox, self.imageseries)
        # for c in range(metadata["SizeC"]):
        #     channel_names.append(
        #         self.ox.image(self.imageseries).Pixels.Channel(c).Name
        #     )
            
        #     self.ox.image(self.imageseries).Pixels.Channel(c).
        metadata = self._remove_none_or_empty_dict(metadata)
        return metadata
    
    @classmethod
    def _parse_channels(cls, sizeC, ox, imageseries):
        channels_dict = {}
        for c in range(sizeC):
            channel_obj = ox.image(imageseries).Pixels.Channel(c)
            channel_name = channel_obj.Name
            channel_dict = {}
            for attr in ["Name",
                         "ID",
                         "SamplesPerPixel",
                         "IlluminationType,",
                         "PinHoleSize",
                         "PinHoleSizeUnit",
                         "AcquisitionMode",
                         "ContrastMethod",
                         "ExcitationWavelength",
                         "ExcitationWavelengthUnit",
                         "EmissionWavelength",
                         "EmissionWavelengthUnit",
                         "Fluor",
                         "NDFilter",
                         "PockelCellSetting",
                         "Color"
                         ]:
                if hasattr(channel_obj, attr):
                    val = getattr(channel_obj, attr)
                    channel_dict[attr] = val
                channel_dict = cls._remove_none_or_empty_dict(channel_dict)
            channels_dict[channel_name] = channel_dict
            
        return channels_dict
            
        
        
    @staticmethod
    def _remove_none_or_empty_dict(dictionary):
        return {key : item for key, item in dictionary.items() if (item != []) and (item != None)}
        
        
    @classmethod
    def _open_tiff(cls, fpath: pathlib.PosixPath) -> (np.ndarray, str):
        with tifffile.TiffFile(str(fpath)) as tif:
            omexml_string = tif.ome_metadata
            array = tif.asarray()

        # array = cls._adjust_array_dims(array)
        return array, omexml_string

    # @staticmethod
    # def _adjust_array_dims(array, n_ch=1, n_t=1, n_z=1):
    #     if n_ch == 1:
    #         array = np.expand_dims(array, axis=-3)
    #     if n_z == 1:
    #         array = np.expand_dims(array, axis=-4)
    #     if n_t == 1:
    #         array = np.expand_dims(array, axis=-5)
    #     return array

    @staticmethod
    def _get_metadata_template():
        metadata = {
            "Directory": None,
            "Filename": None,
            "Extension": None,
            "ImageType": None,
            "AcqDate": None,
            "TotalSeries": None,
            "SizeX": None,
            "SizeY": None,
            "SizeZ": 1,
            "SizeC": 1,
            "SizeT": 1,
            "SizeS": 1,
            "SizeB": 1,
            "SizeM": 1,
            "PhysicalSizeX": None,
            "PhysicalSizeXUnit": None,
            "PhysicalSizeY": None,
            "PhysicalSizeYUnit": None,
            "PhysicalSizeZ": None,
            "PhysicalSizeZUnit": None,
            "Sizes BF": None,
            "DimOrder BF": None,
            "DimOrder BF Array": None,
            "ObjNA": [],
            "ObjMag": [],
            "ObjID": [],
            "ObjName": [],
            "ObjImmersion": [],
            "TubelensMag": [],
            "ObjNominalMag": [],
            "DetectorModel": [],
            "DetectorName": [],
            "DetectorID": [],
            "DetectorType": [],
            "InstrumentID": [],
            "MicroscopeType": [],
            "Channels": [],
            # 'ChannelNames': [],
            # 'ChannelColors': [],
            "ImageIDs": [],
            # "NumPy.dtype": None,
        }

        return metadata


#%%
# basepath = Path("/home/phil/Scrivania")
# cell_path = basepath.joinpath("cell.ome.tiff")
# stack_path = basepath.joinpath("stack.tiff")

# reader = OMETIFFReader(cell_path)
# array, metadata, xml_string = reader.read()
# reader.write_xml()
