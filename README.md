## About

`pyometiff` is a Python library for reading and writing OME-TIFF files that
are compliant with the OME-XML specifications.

`pyometiff` tries to cover most of the tags in the latest [OMEXML format specification](https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome.html), while most of the available Python conversion tools are often missing key tags like `PhysicalSizeXUnit` which are fundamental in any microscopy environment.

## Installation

Run the following to install:

```python
pip install pyometiff
```

## Usage

`pyometiff` exposes two main classes: `OMETIFFReader` and `OMETIFFWriter` which
you can use to read and write OME TIFF files.


To open a OME-TIFF image you can create an `OMETIFFReader`object and call its `.read()` method.


```python
import pathlib
from pyometiff import OMETIFFReader
img_fpath = pathlib.Path("/path/to/img.ome.tiff")

reader = OMETIFFReader(fpath=img_fpath)

img_array, metadata, xml_metadata = reader.read()
```

similarly, to write an OME-TIFF file, we use the `OMETIFFWriter` class and its `.write()` method as in the example.

```python
import pathlib
from pyometiff import OMETIFFWriter
output_fpath = pathlib.Path.cwd().joinpath("test_out.ome.tiff")

# a template metadata dict is available at OMETIFFReader._get_metadata_template()

metadata_dict = {
    "PhysicalSizeX" : "0.88",
    "PhysicalSizeXUnit" : "µm",
    "PhysicalSizeY" : "0.88",
    "PhysicalSizeYUnit" : "µm",
    "PhysicalSizeZ" : "3.3",
    "PhysicalSizeZUnit" : "µm",
    "Channels" : {
        "405" : {
            "Name" : "405nm",
            "SamplesPerPixel": 1,
            "ExcitationWavelength": 405.,
            "ExcitationWavelengthUnit": "nm"
        },
        "488" : {
            "Name" : "488nm",
            "SamplesPerPixel": 1,
            "ExcitationWavelength": 488.,
            "ExcitationWavelengthUnit": "nm"
        },
        "638" : {
            "Name" : "638nm",
            "SamplesPerPixel": 1,
            "ExcitationWavelength": 638.,
            "ExcitationWavelengthUnit": "nm"
        },
    }

# our data in npy format
npy_array_data = np.array(shape=(2, 10, 3, 256, 256))
# a string describing the dimension ordering
dimension_order = "ZTCYX"

writer = OMETIFFWriter(
    fpath=output_fpath,
    dimension_order=dimension_order,
    array=npy_array_data,
    metadata=metadata,
    explicit_tiffdata=False)

writer.write()
```
## Licensing
`pyometiff` is distributed under the **GNU General Public License v3.0** (GNU GPLv3),

see the [LICENSE](LICENSE) file for further information.

This implementation is partially based on
[aicsimageio](https://github.com/AllenCellModeling/aicsimageio) by the Allen Institute for Cell Science and [python-bioformats](https://github.com/CellProfiler/python-bioformats) by the Broad Institute, part of the CellProfiler project.

The relative licensing and copyright notices are included in the [LICENSE](LICENSE) file.

## External Resources
- [The Open Microscopy Environment - OME](https://www.openmicroscopy.org/)
- [OME-TIFF format](https://docs.openmicroscopy.org/ome-model/5.6.3/ome-tiff/)
- [OME-TIFF specification](https://docs.openmicroscopy.org/ome-model/5.5.7/ome-tiff/specification.html)
- [OME-XML format](https://docs.openmicroscopy.org/ome-model/5.6.3/ome-xml/)
- [OME-XML schema specification](https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome.html)

## Contacts

**Author:**

Filippo Maria Castelli  
castelli@lens.unifi.it  
LENS, European Laboratory for Non-linear Spectroscopy  
Via Nello Carrara 1  
50019 Sesto Fiorentino (FI), Italy
