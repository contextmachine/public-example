import importlib
import json
import os
import sys

from mmcore.services.client import get_connection_by_host_port
import asyncio
import functools
import dill

rhconn = get_connection_by_host_port(("localhost", 7778), ("92.53.64.197", 7778))

sys.modules['Rhino'] = rhconn.root.getmodule("Rhino")
sys.modules['Rhino.Geometry'] = rhconn.root.getmodule("Rhino.Geometry")


def point_to_dict(pt):
    return dict(zip(("x", "y", "z"), (pt.X, pt.Y, pt.Z)))


def pts_to_dicts(pts): return [point_to_dict(pt) for pt in pts]


class Binder:
    def __init__(self, conn, module="", decoder=lambda x: x):
        self.target_module = importlib.import_module(module)
        self.conn = conn
        self.decoder = decoder
        self.conn.root.execute(dill.source.getsource(self.target_module))

    def __call__(self, obj):
        self.conn.root.execute("\n".join(dill.source.getsource(obj).split('\n')[1:]))

        @functools.wraps(obj)
        def wrap(**params):
            self.conn.root.execute(f"params = {params};result = {obj.__name__}(**params)")
            return self.decoder(self.conn.root.namespace["result"])

        return wrap
import copy


def decode_axis(axis):
    def decode_line(cls):
        if isinstance(axis, list) and (len(axis)>1):


            return list(map(lambda line: cls(*line["line"], extrusion=line["extrusion"]), copy.deepcopy(axis)))
        else:
            raise Exception(axis)
    return decode_line


@Binder(conn=rhconn, module="models.axis", decoder=decode_axis)
def solve(curves, t0=0.0, t1=0.0, h=600.0):
    try:
        crv0, crv1 = generate_polyline(curves[0]).ToNurbsCurve(), generate_polyline(curves[1]).ToNurbsCurve()
        cells = CellingGenerator((crv0, crv1), (t0, t1), h)

        return list(cells)
    except Exception as err:
        return err
