import os,sys,inspect
from pathlib import Path
import pytest
from mock import patch
import pudb
import tifffile
import numpy as np
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from pyometiff.omewriter import OMETIFFWriter
from pyometiff.omereader import OMETIFFReader

#TODO: implement readback tests

parentdir_path = Path(parentdir)
test_img_path = parentdir_path.joinpath("tests/cell.ome.tiff")
test_out_path = parentdir_path.joinpath("tests/test_out.ome.tiff")

metadata = {'Directory': None,
        # 'Filename': None,
        # 'Extension': None,
        # 'ImageType': None,
        # 'AcqDate': None,
        # 'TotalSeries': None,
        # 'SizeX': None,
        # 'SizeY': None,
        # 'SizeZ': 1,
        # 'SizeC': 1,
        # 'SizeT': 1,
        # 'SizeS': 1,
        # 'SizeB': 1,
        # 'SizeM': 1,
        'PhysicalSizeX': 1,
        'PhysicalSizeXUnit': "µm",
        'PhysicalSizeY': 1,
        'PhysicalSizeYUnit': "µm",
        'PhysicalSizeZ': 1,
        'PhysicalSizeZUnit': "µm",
        # 'Sizes BF': None,
        # 'DimOrder BF': None,
        # 'DimOrder BF Array': None,
        # 'ObjNA': [],
        # 'ObjMag': [],
        # 'ObjID': [],
        # 'ObjName': [],
        # 'ObjImmersion': [],
        # 'TubelensMag': [],
        # 'ObjNominalMag': [],
        # 'DetectorModel': [],
        # 'DetectorName': [],
        # 'DetectorID': [],
        # 'DetectorType': [],
        # 'InstrumentID': [],
        # "MicroscopeType": [],
        'Channels': {
            "405": {"SamplesPerPixel": 1},
            "488": {"SamplesPerPixel": 1},
            "638": {"SamplesPerPixel": 1}},
        # 'ChannelNames': [],
        # 'ChannelColors': [],
        # 'ImageIDs': [],
        # 'NumPy.dtype': None
        }


class TestOMETIFFWriter:
    
    @pytest.fixture
    def clean_fixture(self):
        test_out_path.unlink(missing_ok=True)
        yield
        test_out_path.unlink(missing_ok=True)
    
    def test_init(self) -> None:
        array = np.zeros(shape=(2, 10, 3, 20, 20))
        writer = OMETIFFWriter(fpath=test_out_path,
                                array=array,
                                metadata=metadata)
        
    def test_write(self, clean_fixture) -> None:
        shape = (2, 10, 3, 20, 20)
        array = np.zeros(shape)
        writer = OMETIFFWriter(fpath=test_out_path,
                                array=array,
                                metadata=metadata)
        writer.write()
        assert test_out_path.exists(), "file was not generated"
        arr = tifffile.imread(test_out_path)
        # pudb.set_trace()
        # this should not work when images miss some channels
        # TODO: implement read case for images with less channels
        assert arr.shape == shape, "invalid reconstructed shape"
        
        
        
                               