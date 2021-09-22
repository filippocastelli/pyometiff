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
from lxml import etree as ET
import numpy as np
import tifffile
from pyometiff.omexml import OMEXML, get_pixel_type, xsd_now

BYTE_BOUNDARY = 2 ** 21


class InvalidDimensionOrderingError(Exception):
    """exception for invalid dimensional ordering"""

    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self.message = message

    def __str__(self):
        return self.message


class OMETIFFWriter:
    def __init__(
        self,
        fpath: Path,
        array: np.ndarray,
        metadata: dict,
        overwrite: bool = False,
        dimension_order: str = "STZCYX",
        photometric: str = "minisblack",
        explicit_tiffdata: bool = False,
        compression=None
        
    ):
        self.fpath = Path(fpath)
        self.array = array
        self.metadata = metadata
        self.overwrite = overwrite
        self.dimension_order = dimension_order
        self.photometric = photometric
        self.explicit_tiffdata = explicit_tiffdata
        self.compression = compression
        
    def write(self):
        self._array, self._dimension_order = self._adjust_dims(
            self.array, self.dimension_order
        )
        self._ox = self.gen_meta()
        self._xml = self._ox.to_xml().encode()
        self.write_stack(self._array, self._xml)

    def write_xml(self):
        self._ox = self.gen_meta()
        self._xml = self._ox.to_xml().encode()
        xml_fpath = self.fpath.parent.joinpath(self.fpath.stem + ".xml")
        tree = ET.ElementTree(ET.fromstring(self._xml))
        tree.write(str(xml_fpath), encoding="utf-8", method="xml", pretty_print=True)

    @staticmethod
    def _use_bigtiff(array):
        if array is None:
            return False
        else:
            file_size = array.size * array.itemsize
            return file_size > BYTE_BOUNDARY

    def write_stack(self, array, xml_meta):
        self.use_bigtiff = self._use_bigtiff(array)
        self.use_bigtiff = True
        with tifffile.TiffWriter(str(self.fpath), bigtiff=self.use_bigtiff) as tif:
            tif.save(
                array, description=xml_meta, photometric=self.photometric, metadata=None, compression=self.compression
            )

    def gen_meta(self):
        ox = OMEXML()
        ox.image().set_ID("Image:0")
        
        pixels = ox.image().Pixels

        # pixels.ome_uuid = ox.uuidStr
        pixels.set_ID("Pixels:0")

        # trying first to set all items
        error_keys = []
        metadata_dict_cpy = self.metadata.copy()
        
        exp_keys = ["Channels", "Name", "AcquisitionDate"]
        pop_expected_keys = {key: metadata_dict_cpy.pop(key, None) for key in exp_keys}
        
        # set image acquisitiondate
        acq_date = pop_expected_keys["AcquisitionDate"]
        acq_date = acq_date if acq_date is not None else xsd_now()
        ox.image().set_AcquisitionDate(acq_date)
        
        img_name = pop_expected_keys["Name"]
        img_name = img_name if img_name is not None else "pyometiff_exported"
        
        ox.image().set_Name(img_name)
        
        for key, item in metadata_dict_cpy.items():
            try:
                setattr(pixels, key, item)
            except AttributeError:
                error_keys.append(key)
                print("could not set key {} to {}".format(key, str(item)))

        shape = self._array.shape

        def _dim_or_1(dim):
            idx = self._dimension_order.find(dim)
            return 1 if idx == -1 else shape[idx]

        pixels.channel_count = _dim_or_1("C")
        pixels.set_SizeT(_dim_or_1("T"))
        pixels.set_SizeC(_dim_or_1("C"))
        pixels.set_SizeZ(_dim_or_1("Z"))
        pixels.set_SizeY(_dim_or_1("Y"))
        pixels.set_SizeX(_dim_or_1("X"))

        # this is reversed of what dimensionality of the ometiff file is saved as
        pixels.set_DimensionOrder(self._dimension_order[::-1])

        # convert numpy dtype to a compatibile pixeltype
        pixels.set_PixelType(get_pixel_type(self._array.dtype))

        if pop_expected_keys["Channels"] is not None:
            channels_dict = pop_expected_keys["Channels"]
            assert (
                len(channels_dict.keys()) == pixels.SizeC
            ), "Channel label count is different than channel count"
            self._parse_channel_dict(pixels, channels_dict)
        else:
            for i in range(pixels.SizeC):
                pixels.Channel(i).set_ID("Channel:0:" + str(i))
                pixels.Channel(i).set_Name("C:" + str(i))

        pixels.populate_TiffData(explicit=self.explicit_tiffdata)

        return ox

    @staticmethod
    def _parse_channel_dict(pixels, channels_dict):
        channel_names = list(channels_dict.keys())
        channels_ignored_keys = {}
        for idx, channel_name in enumerate(channel_names):
            channel_dict = channels_dict[channel_name]
            pixels.Channel(idx).set_ID("Channel:0" + str(idx))
            pixels.Channel(idx).set_Name(channel_name)

            if "SamplesPerPixel" not in channel_dict:
                pixels.Channel(idx).set_SamplesPerPixel(1)

            channel_ignored_keys = []
            for channel_key, item in channel_dict.items():
                try:
                    setattr(pixels.Channel(idx), channel_key, item)
                except AttributeError:
                    channel_ignored_keys.append(channel_key)

            channels_ignored_keys[channel_name] = channel_ignored_keys

    @staticmethod
    def _adjust_dims(array, dimension_order):
        array_shape = array.shape
        ndims = len(array_shape)

        assert ndims in (3, 4, 5), "Expected a 3, 4, or 5-dimensional array"

        # no strange dim names
        if not (all(d in "STCZYX" for d in dimension_order)):
            raise InvalidDimensionOrderingError(
                "Invalid dimension_order {}".format(dimension_order)
            )

        # ends in YX
        if dimension_order[-2:] != "YX":
            raise InvalidDimensionOrderingError(
                "the last two dimensions are expected to be YX, they are {} instead. Please transpose your data".format(
                    dimension_order[-2:]
                )
            )

        # starts in S
        if dimension_order.find("S") > 0:
            raise InvalidDimensionOrderingError(
                "S must be the leading dim in dimension_order {}".format(
                    dimension_order
                )
            )

        # enough dimensions
        if len(dimension_order) < ndims:
            raise InvalidDimensionOrderingError(
                "dimension_order {} must have at least as many dimensions as array shape {}".format(
                    dimension_order, array_shape
                )
            )

        # no letter appears more than once
        if len(set(dimension_order)) != len(dimension_order):
            raise InvalidDimensionOrderingError(
                "A letter appears more than once in dimension_order {}".format(
                    dimension_order
                )
            )

        # trim dimension order to match array
        # if array is [T,C,Z,Y,X], dimension_order STCZYX becomes TCZYX
        if len(dimension_order) > ndims:
            dimension_order = dimension_order[-ndims:]

        # expand 3D data to 5D
        if ndims == 3:
            # expand double
            array = np.expand_dims(array, axis=0)
            array = np.expand_dims(array, axis=0)
            # prepend either TC, TZ or CZ
            if dimension_order[0] == "T":
                dimension_order = "CZ" + dimension_order
            elif dimension_order[0] == "C":
                dimension_order = "TZ" + dimension_order
            elif dimension_order[0] == "Z":
                dimension_order = "TC" + dimension_order

        # if it's 4D expand to 5D
        elif ndims == 4:
            array = np.expand_dims(array, axis=0)
            # prepend either T, C, or Z
            first2 = dimension_order[:2]
            if first2 == "TC" or first2 == "CT":
                dimension_order = "Z" + dimension_order
            elif first2 == "TZ" or first2 == "ZT":
                dimension_order = "C" + dimension_order
            elif first2 == "CZ" or first2 == "ZC":
                dimension_order = "T" + dimension_order

        return array, dimension_order
