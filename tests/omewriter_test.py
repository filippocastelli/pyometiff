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

npy_metadata_dict = {'Directory': None,
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
            "405": {"Name": "405",
                    "SamplesPerPixel": 1,
                    "ExcitationWavelength": 405.,
                    "ExcitationWavelengthUnit": "nm"},
            "488": {"Name": "488",
                    "SamplesPerPixel": 1,
                    "ExcitationWavelength": 488.,
                    "ExcitationWavelengthUnit": "nm"},
            "638": {"Name": "638",
                    "SamplesPerPixel": 1,
                    "ExcitationWavelength": 638.,
                    "ExcitationWavelengthUnit": "nm"},
                        }
        # 'ChannelNames': [],
        # 'ChannelColors': [],
        # 'ImageIDs': [],
        # 'NumPy.dtype': None
        }

npy_array = np.zeros(shape=(2, 10, 3, 20, 20))
npy_dimension_order = ["STZCYX", "TZCYX"]
test_img_array, test_img_metadata, _ = OMETIFFReader(fpath=test_img_path).read()
test_img_dimorder = test_img_metadata["DimOrder"]

testdata = [
    (npy_array, npy_dimension_order[0], npy_metadata_dict),
    (npy_array, npy_dimension_order[1], npy_metadata_dict),
    (test_img_array, test_img_dimorder, test_img_metadata)
    ]


class TestOMETIFFWriter:
    
    @pytest.fixture
    def clean_fixture(self):
        test_out_path.unlink(missing_ok=True)
        yield
        test_out_path.unlink(missing_ok=True)
    
    def test_init(self) -> None:
        array = np.zeros(shape=(2, 10, 3, 20, 20))
        dimension_order = "STZCYX"
        writer = OMETIFFWriter(fpath=test_out_path,
                                array=array,
                                metadata=npy_metadata_dict,
                                dimension_order=dimension_order)
         
        assert writer.fpath == Path(test_out_path)
        
    def test_write(self, clean_fixture) -> None:
        shape = (2, 10, 3, 20, 20)
        array = np.zeros(shape)
        writer = OMETIFFWriter(fpath=test_out_path,
                                array=array,
                                metadata=npy_metadata_dict)
        writer.write()
        assert test_out_path.exists(), "file was not generated"
        arr = tifffile.imread(test_out_path)
        # pudb.set_trace()
        # this should not work when images miss some channels
        # TODO: implement read case for images with less channels
        assert arr.shape == shape, "invalid reconstructed shape"
    
    
    id_params = ["with_S", "without_S", "load"]
    @pytest.mark.parametrize("data, param_id", zip(testdata, id_params), ids = lambda x: x[1])
    def test_readback(self, data, param_id, clean_fixture) -> None:
        
        # if param_id == "load":
            # pudb.set_trace()
            # pass
        array, dimorder, metadata = data
        shape = array.shape
        writer = OMETIFFWriter(fpath=test_out_path,
                               array=array,
                               metadata=metadata,
                               dimension_order=dimorder)
        writer.write()
        reader = OMETIFFReader(test_out_path)
        array_readback, metadata_readback, metadata_xml_readback = reader.read()
        
        # check shape
        assert array.shape == array_readback.shape, "Different shapes"
        
        # check dims
        check_dim_order = self._remove_s_from_dim_order(dimorder)
        dims = {dim : self._get_size(dim, check_dim_order, shape) for dim in check_dim_order}
        
        assert check_dim_order == metadata_readback["DimOrder"]
        
        retrieved_dims = {
            "T": metadata_readback["SizeT"],
            "Z": metadata_readback["SizeZ"],
            "C": metadata_readback["SizeC"],
            "Y": metadata_readback["SizeY"],
            "X": metadata_readback["SizeX"]
            }
            
        for key, item in dims.items():
            assert item == retrieved_dims[key], "different dim reconstruction"
        
        # Physical Size and Unit
        for dim in ["X", "Y", "Z"]:
            key = "PhysicalSize" + dim
            key_unit = key + "Unit"
            assert metadata_readback[key] == metadata[key]
            assert metadata_readback[key_unit] == metadata[key_unit]
            
        # paths
        assert str(test_out_path.name) == metadata_readback["Filename"], "Different filename retrieved"
        assert str(test_out_path.parent) == metadata_readback["Directory"], "Different directory retrieved"

        # pudb.set_trace()
        
    @staticmethod
    def _remove_s_from_dim_order(dim_order):
        if "S" in dim_order:
            dim_order = dim_order.replace("S", "")
        return dim_order

    @staticmethod
    def _get_size(dim, dim_order, shape):
        idx = dim_order.find(dim)
        return shape[idx]
        
        
                               