from pathlib import Path
from lxml import etree as ET

from omexml import OMEXML

import tifffile
import numpy as np


#%%
class OMETIFFReader:
    
    def __init__(
            self,
            fpath,
            imageseries=0):
        self.fpath = Path(fpath)
        self.imageseries = imageseries
        
    def read(self):
        self.array, self.omexml_string = self._open_tiff(self.fpath)
        self.metadata = self.parse_metadata(self.omexml_string)
        return self.array, self.metadata, self.omexml_string
    
    
    def write_xml(self):
        if not hasattr(self, "omexml_string"):
            _, _, _ = self.read()
        xml_fpath = self.fpath.parent.joinpath(self.fpath.stem+".xml")
        tree = ET.ElementTree(ET.fromstring(self.omexml_string.encode("utf-8")))
        tree.write(str(xml_fpath), encoding="utf-8", method="xml", pretty_print=True)
        
    def parse_metadata(self, omexml_string):
        self.ox = OMEXML(self.omexml_string)
        metadata = self._get_metadata_template()
        
        metadata["Directory"] = str(self.fpath.parent)
        metadata["Filename"] = str(self.fpath.name)
        metadata["Extension"] = "ome.tiff"
        metadata["ImageType"] = "ometiff"
        metadata["AcqDate"] = self.ox.image(self.imageseries).AcquisitionDate
        metadata["Name"] = self.ox.image(self.imageseries).Name
        
        # image dimensions
        metadata["SizeT"] = self.ox.image(self.imageseries).Pixels.SizeT
        metadata["SizeZ"] = self.ox.image(self.imageseries).Pixels.SizeZ
        metadata["SizeC"] = self.ox.image(self.imageseries).Pixels.SizeC
        metadata["SizeX"] = self.ox.image(self.imageseries).Pixels.SizeX
        metadata["SizeY"] = self.ox.image(self.imageseries).Pixels.SizeY
        
        # number of image series
        metadata["TotalSeries"] = self.ox.get_image_count()
        metadata["Sizes BF"] = [metadata["TotalSeries"],
                                metadata["SizeT"],
                                metadata["SizeZ"],
                                metadata["SizeC"],
                                metadata["SizeY"],
                                metadata["SizeX"]]
        
        # get number of image series
        metadata['TotalSeries'] = self.ox.get_image_count()
        metadata['Sizes BF'] = [metadata['TotalSeries'],
                                metadata['SizeT'],
                                metadata['SizeZ'],
                                metadata['SizeC'],
                                metadata['SizeY'],
                                metadata['SizeX']]

        # get dimension order
        metadata['DimOrder BF'] = self.ox.image(self.imageseries).Pixels.DimensionOrder
    
        # reverse the order to reflect later the array shape
        metadata['DimOrder BF Array'] = metadata['DimOrder BF'][::-1]
        
        # DimOrder custom field 
        metadata["DimOrder"] = metadata["DimOrder BF Array"]
    
        # get the scaling
        metadata['XScale'] = self.ox.image(self.imageseries).Pixels.PhysicalSizeX
        metadata['XScale'] = np.round(metadata['XScale'], 3)
        
        metadata['YScale'] = self.ox.image(self.imageseries).Pixels.PhysicalSizeY
        metadata['YScale'] = np.round(metadata['YScale'], 3)
        
        metadata['ZScale'] = self.ox.image(self.imageseries).Pixels.PhysicalSizeZ
        metadata['ZScale'] = np.round(metadata['ZScale'], 3)
    
        # get all image IDs
        for i in range(self.ox.get_image_count()):
            metadata['ImageIDs'].append(i)
        # get information about the instrument and objective
        try:
            metadata['InstrumentID'] = self.ox.instrument(self.imageseries).get_ID()
        except (KeyError, AttributeError) as e:
            print('Key not found:', e)
            metadata['InstrumentID'] = None
        try:
            metadata['DetectorModel'] = self.ox.instrument(self.imageseries).Detector.get_Model()
            metadata['DetectorID'] = self.ox.instrument(self.imageseries).Detector.get_ID()
            metadata['DetectorModel'] = self.ox.instrument(self.imageseries).Detector.get_Type()
        except (KeyError, AttributeError) as e:
            print('Key not found:', e)
            metadata['DetectorModel'] = None
            metadata['DetectorID'] = None
            metadata['DetectorModel'] = None
    
        try:
            metadata['ObjNA'] = self.ox.instrument(self.imageseries).Objective.get_LensNA()
            metadata['ObjID'] = self.ox.instrument(self.imageseries).Objective.get_ID()
            metadata['ObjMag'] = self.ox.instrument(self.imageseries).Objective.get_NominalMagnification()
        except (KeyError, AttributeError) as e:
            print('Key not found:', e)
            metadata['ObjNA'] = None
            metadata['ObjID'] = None
            metadata['ObjMag'] = None
    
        # get channel names
        for c in range(metadata['SizeC']):
            metadata['Channels'].append(self.ox.image(self.imageseries).Pixels.Channel(c).Name)
            
        return metadata            

    @classmethod
    def _open_tiff(cls, fpath):
        with tifffile.TiffFile(str(fpath)) as tif:
            omexml_string = tif.ome_metadata
            array = tif.asarray()
            
        array = cls._adjust_array_dims(array)
        return array, omexml_string
    
    @staticmethod
    def _adjust_array_dims(array, n_ch=1, n_t=1, n_z=1):
        if n_ch == 1:
            array = np.expand_dims(array, axis=-3)
        if n_z == 1:
            array = np.expand_dims(array, axis=-4)
        if n_t == 1:
            array = np.expand_dims(array, axis=-5)
        return array
            
    @staticmethod
    def _get_metadata_template():
        metadata = {'Directory': None,
                    'Filename': None,
                    'Extension': None,
                    'ImageType': None,
                    'AcqDate': None,
                    'TotalSeries': None,
                    'SizeX': None,
                    'SizeY': None,
                    'SizeZ': 1,
                    'SizeC': 1,
                    'SizeT': 1,
                    'SizeS': 1,
                    'SizeB': 1,
                    'SizeM': 1,
                    'Sizes BF': None,
                    'DimOrder BF': None,
                    'DimOrder BF Array': None,
                    'Axes_czifile': None,
                    'Shape_czifile': None,
                    'czi_isRGB': None,
                    'czi_isMosaic': None,
                    'ObjNA': [],
                    'ObjMag': [],
                    'ObjID': [],
                    'ObjName': [],
                    'ObjImmersion': [],
                    'TubelensMag': [],
                    'ObjNominalMag': [],
                    'XScale': None,
                    'YScale': None,
                    'ZScale': None,
                    'XScaleUnit': None,
                    'YScaleUnit': None,
                    'ZScaleUnit': None,
                    'DetectorModel': [],
                    'DetectorName': [],
                    'DetectorID': [],
                    'DetectorType': [],
                    'InstrumentID': [],
                    'Channels': [],
                    # 'ChannelNames': [],
                    # 'ChannelColors': [],
                    'ImageIDs': [],
                    'NumPy.dtype': None
                    }
    
        return metadata
    
#%%
basepath = Path("/home/phil/Scrivania")
cell_path = basepath.joinpath("cell.ome.tiff")
stack_path = basepath.joinpath("stack.tiff")

reader = OMETIFFReader(cell_path)
array, metadata, xml_string = reader.read()
reader.write_xml()