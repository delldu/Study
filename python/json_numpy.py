import base64
import json
import numpy
import pdb


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            if obj.flags["C_CONTIGUOUS"]:
                data_b64 = base64.b64encode(obj.data)
            else:
                data_b64 = base64.b64encode(numpy.ascontiguousarray(obj))
            return dict(
                shape=obj.shape, dtype=str(obj.dtype), ndarray=data_b64.decode("utf-8")
            )


def numpy_encode(array):
    return json.dumps(array, cls=NumpyEncoder)


def numpy_decode(jsons):
    def json_numpy_obj_hook(dct):
        if isinstance(dct, dict) and "ndarray" in dct:
            data = base64.b64decode(dct["ndarray"])
            return numpy.frombuffer(data, dct["dtype"]).reshape(dct["shape"])
        return dct

    return json.loads(jsons, object_hook=json_numpy_obj_hook)


array = numpy.arange(100, dtype=numpy.float).reshape(2, 50)
dumped = numpy_encode(array)
result = numpy_decode(dumped)

pdb.set_trace()


# None of the following assertions will be broken.
assert result.dtype == array.dtype, "Wrong Type"
assert result.shape == array.shape, "Wrong Shape"
assert numpy.allclose(array, result), "Wrong Values"
