import pathlib
import datetime
from pyometiff import OMETIFFWriter
import numpy as np
output_fpath = pathlib.Path.cwd().joinpath("test_out.ome.tiff")

# a template metadata dict is available at OMETIFFReader._get_metadata_template()

metadata_dict = {
    # "AcquisitionDate": str(datetime.datetime.now().isoformat()),
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
}
# our data in npy format
npy_array_data = np.zeros(shape=(2, 10, 3, 256, 256))
# a string describing the dimension ordering
dimension_order = "ZTCYX"

writer = OMETIFFWriter(
    fpath=output_fpath,
    dimension_order=dimension_order,
    array=npy_array_data,
    metadata=metadata_dict,
    explicit_tiffdata=False)

writer.write()
writer.write_xml()