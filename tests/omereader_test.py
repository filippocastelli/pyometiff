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

import sys
import os
import inspect
from pathlib import Path
import pytest
from mock import patch

import numpy as np

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from pyometiff.omereader import OMETIFFReader

parentdir_path = Path(parentdir)
test_img_path = parentdir_path.joinpath("tests/cell.ome.tiff")


class MockedOMEXML:

    def __init__(self, arg):
        pass

    class Image:
        AcquisitionDate = "today"
        Name = "mock_pixels"

        class Pixels:
            def __init__(self):
                pass

            AcquisitionDate = "today"
            Name = "mock_pixels"
            SizeT = 10
            SizeC = 2
            SizeZ = 15
            SizeX = 256
            SizeY = 256
            PhysicalSizeX = "1.0"
            PhysicalSizeY = "1.0"
            PhysicalSizeZ = "1.0"
            PhysicalSizeXUnit = "µm"
            PhysicalSizeYUnit = "µm"
            PhysicalSizeZUnit = "µm"
            DimensionOrder = "XYCZT"

            class Channel:
                def __init__(self, int_arg):
                    pass

                Name = "channel_name"

    class Instrument:
        def __init__(self):
            pass

        @staticmethod
        def get_ID():
            return "instrument_ID"

        class Objective:
            def __init__(self):
                pass

            @staticmethod
            def get_ID():
                return "objective_ID"

            @staticmethod
            def get_LensNA():
                return "lens_NA"

            @staticmethod
            def get_NominalMagnification():
                return "nominal_magnification"

        class Microscope:
            def __init__(self):
                pass

            @staticmethod
            def get_Type():
                return "mocked_microscope"

        class Detector:
            def __init__(self):
                pass

            @staticmethod
            def get_Model():
                return "detector_model"

            @staticmethod
            def get_ID():
                return "detector_ID"

            @staticmethod
            def get_Type():
                return "mocked_detector"

    def image(self, imageseries=0):
        return self.Image()

    def instrument(self, imageseries=0):
        return self.Instrument()

    @staticmethod
    def get_image_count():
        return 1


class TestOMETIFFReader:
    @pytest.fixture
    def read_fixture(self, **kwargs):
        def _read_fixture(**_kwargs):
            reader = OMETIFFReader(**kwargs)
            reader.read()
            return reader.array, reader.metadata, reader.omexml_string

        return _read_fixture

    @staticmethod
    def mock_OMEXML():
        return 0

    def test_init(self) -> None:
        reader = OMETIFFReader(fpath=test_img_path)
        assert reader.fpath == test_img_path
        assert reader.imageseries == 0

    def test_read(self) -> None:
        reader = OMETIFFReader(fpath=test_img_path)
        array, metadata, omexml_string = reader.read()
        # pudb.set_trace()
        assert type(array) == np.ndarray
        assert len(metadata.keys()) > 0

    def test_open_tiff(self) -> None:
        array, omexml_string = OMETIFFReader._open_tiff(fpath=test_img_path)
        assert array.shape == (10, 15, 2, 256, 256)
        assert omexml_string != ""

    def test_with_fixture(self, read_fixture) -> None:
        array, metadata, omexml_string = read_fixture(fpath=test_img_path)

    @patch('pyometiff.omereader.OMEXML', side_effect=MockedOMEXML)
    def test_parse_metadata(self, mock_object):
        # mock_omexml.get.side_effect = 1
        reader = OMETIFFReader(fpath=test_img_path)
        # pudb.set_trace()
        _, _, _ = reader.read()
