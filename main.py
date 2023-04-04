import copy
import uuid
import dotenv
dotenv.load_dotenv(dotenv.find_dotenv(".env", usecwd=True),override=False)
import fontTools.varLib.instancer
from mmcore.gql import client as graphql_client

from mmcore.baseitems import Matchable

import json
from mmcore.gql.client import GQLReducedFileBasedQuery
import strawberry
from strawberry.scalars import JSON, Dict
from enum import Enum
from mmcore.collections.multi_description import ElementSequence

from strawberry.fastapi import GraphQLRouter

from mmcore.gql.client import GQLReducedFileBasedQuery, GQLReducedQuery

from mmcore.services.redis import stream
from mmcore.node import node_eval
from mmcore.geom.materials import ColorRGB, MeshPhongFlatShading
import os
import redis


def get_cloud_connection(host=os.getenv("REDIS_HOST"),
                         port=os.getenv("REDIS_PORT"),
                         password=os.getenv("REDIS_PASSWORD"),
                         db=0):
    return redis.StrictRedis(host=host, port=int(port), password=password, db=db)


conn = get_cloud_connection()
conn.ping()
param_stream = stream.SharedDict(os.getenv("CXM_REDIS_PARAM_STREAM"), conn)

import json

_points_query = GQLReducedFileBasedQuery(path="temp/query_BasePointsQuery.gql")


class GQLYaml(GQLReducedQuery):
    @property
    def yaml(self):
        return self.stream(lambda x: yaml.unsafe_load(x))

    def __init__(self, stream, *args, **kwargs):
        self.stream = stream
        super().__init__(self.yaml["query"], *args, **kwargs)

    def __call__(self):
        return [GQLReducedQuery.__call__(self, variables=x) for x in self.yaml["variables"]]


def points_query(**kwargs):
    res = ElementSequence(_points_query(variables=kwargs))
    sorted_pts = []
    for nm in kwargs.get("points"):
        sorted_pts.append(res.get_from_index(res.search_from_key_value("name", nm)))
    return sorted_pts


@node_eval
def threeLines(points, colors, width=1):
    # print(points,colors)
    with open("temp/lines.js") as codefile:
        lines_code = codefile.read()
    for pts, color in zip(points, colors):
        lines_code += f'makeAxis({pts}, {color}, {width});'
    lines_code += f'console.log(JSON.stringify(mygroup.toJSON()));'
    return lines_code


@node_eval
def threeAxis(lines, color, width=1):
    with open("temp/lines.js") as codefile:
        lines_code = codefile.read()
    for line in lines:
        lines_code += f'makeAxis([{line.a}, {line.b}], {color}, {width});'
    lines_code += f'console.log(JSON.stringify(mygroup.toJSON()));'
    return lines_code


@node_eval
def threeAxisTwo(lines, color, width=1):
    with open("temp/lines.js") as codefile:
        lines_code = codefile.read()
    for line in lines:
        lines_code += f'makeAxis([{line.a}, {line.b}], {json.dumps(line.extrusion)}, {color}, {width});'
    lines_code += f'console.log(JSON.stringify(mygroup.toJSON()));'
    return lines_code


def resolve_mat(obj):
    mat = obj["materials"][0]
    obj["materials"] = [mat]
    for chld in obj["object"]['children']:
        chld["material"] = mat["uuid"]


def merge_groups(first, second):
    first["object"]["children"].append(second["object"])
    first["geometries"].extend(second["geometries"])
    first["materials"].extend(second["materials"])


def generate_three_axis(lines, lines_color=ColorRGB(220, 120, 20).decimal, part="SW", common_name="Опорный профиль-1"):
    th = threeAxis(lines, lines_color)

    # print(th.keys())
    resolve_mat(th)

    for i, ln in enumerate(lines):
        ext = ln.extrusion
        th["materials"].extend(ext["materials"])
        th["geometries"].extend(ext["geometries"])
        ext["object"]["name"] = f"{common_name} {part}-{i}"
        th["object"]["children"].append(ext["object"])
    th["object"]['name'] = f"{part} Axis"
    # print(json.dumps(th,indent=3))
    return th


def generate_three_lines(points, colors, part="SW"):
    lns = threeLines(points, colors)
    lns["object"]["matrix"] = [0.001, 0, 0, 0, 0, 0.001, 0, 0, 0, 0, 0.001, 0, 0, 0, 0, 0.001]
    lns["object"]["name"] = f"{part} Ceiling"
    return lns


from scipy.spatial.distance import euclidean
from models import solve


class MyLine(Matchable):
    __match_args__ = "a", "b"

    def __init__(self, a, b, extrusion, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.a = a
        self.b = b
        self.extrusion = extrusion
        mat = MeshPhongFlatShading(ColorRGB(95, 170, 90))
        self.extrusion["object"]["material"] = mat.uuid
        self.extrusion["materials"].append(mat.data)

    def length(self):
        return euclidean(list(self.a.values()), list(self.b.values()))

    def __repr__(self):
        return f"Line({self.a}, {self.b})"


@strawberry.enum
class MFBPart(str, Enum):
    SW = "SW"
    NE = "NE"


@strawberry.type
class UserData:
    properties: JSON | None = None
    gui: JSON | None = None


@strawberry.type
class Object(Matchable):
    uuid: str

    matrix: list[float]
    up: list[float] | None = None
    userData: UserData | None = None
    geometry: str | None = None
    material: str | None = None
    children: list['Object'] | None = None
    name: str | None = None
    layers: int = 1
    castShadow: bool | None = None
    receiveShadow: bool | None = None
    type: str = "Object3D"


@strawberry.type
class Geometry:
    uuid: str
    data: JSON
    type: str = "BufferGeometry"


@strawberry.type
class Object3D:
    object: Object
    metadata: JSON
    geometries: list[Geometry]
    materials: list[JSON]


@strawberry.type
class Point:
    x: float
    y: float
    z: float


@strawberry.type
class BasePoint:
    x: float
    y: float
    z: float
    id: int
    name: str
    part: MFBPart


@strawberry.input
class BaseAxis:
    part: MFBPart
    points: list[str]

    def todict(self):
        return {"points": self.points, "part": self.part}


def to_obj(objs):
    if isinstance(objs, dict):
        if "children" in objs.keys():
            children = to_obj(objs["children"])
            obj = Object(**objs)
            obj.children = children
            return obj
        elif "type" in objs.keys():
            return Object(**objs)
        else:
            return objs
    elif isinstance(objs, list):
        return [to_obj(ob) for ob in objs]
    else:
        return objs


@strawberry.type
class Line:
    a: Point
    b: Point

    def __init__(self, a, b):
        super().__init__()
        self.a, self.b = a, b


class Param:
    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        param_stream[self.name] = value
        param_stream.commit()

    def __get__(self, inst, own):
        return param_stream.get(self.name)


class AxisPoints(Param):
    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)
        p = Param()
        setattr(owner, "_" + self.name, p)
        p.__set_name__(owner, "_" + self.name)
        param_stream.commit()

    def __get__(self, inst, own):
        return points_query(**param_stream[self.name])

    def __set__(self, instance, value):
        super().__set__(instance, value)
        setattr(instance, "_" + self.name, value)


from mmcore.baseitems import descriptors


@strawberry.type
class Grid:
    def __init__(self, obj):
        self.obj = obj

    @strawberry.field
    def object3d(self) -> Object3D:
        # print(self)
        dct = {}
        dct["geometries"] = [Geometry(**gm) for gm in self.obj._root["geometries"]]

        dct["materials"] = self.obj._root["materials"]
        dct["object"] = {}
        dct["object"]["children"] = [Object(**ob) for ob in self.obj._root["object"]["children"]]
        dct["object"] = to_obj(self.obj._root["object"])
        dct["object"].uuid = self.obj.uuid
        dct["object"].userData = UserData(**self.obj.userdata)
        dct["metadata"] = self.obj._root["metadata"]

        return Object3D(**dct)

    @strawberry.field
    def lines(self) -> Object3D:
        return Object3D(**self.obj._lines)

    @strawberry.field
    def axis(self) -> Object3D:
        return Object3D(**self.obj._axis)

    @strawberry.field
    def all(self) -> JSON:
        return self.obj._root

    @strawberry.field
    def params(self) -> JSON:
        return self.obj.inp_params


class MFBGrid(Matchable):
    __match_args__ = "points_a", "points_b", "t0", "t1", "h"
    properties = descriptors.UserDataProperties("t0", "t1", "h", "part", "first_rail", "second_rail")
    points_a = AxisPoints()
    points_b = AxisPoints()
    t0 = Param()
    t1 = Param()
    h = Param()

    @property
    def first_rail(self):
        return self._points_a["points"]

    @property
    def second_rail(self):
        return self._points_b["points"]

    def __copy__(self):
        obj = super().__copy__()
        uid = uuid.uuid4()
        obj.stream_name = ":".join(self.stream_name.split(":")[:-1] + (uid,))
        obj.strm = stream.ThreeJsSharedDict(obj.stream_name, self.redis_conn)
        return obj

    @property
    def params(self):
        return dict(curves=(self.points_a, self.points_b),
                    t0=self.t0, t1=self.t1, h=self.h)

    @property
    def inp_params(self):
        return dict(points_a=self._points_a, points_b=self._points_b,
                    t0=self.t0, t1=self.t1, h=self.h)

    def __init__(self, *args, stream_name=os.getenv("CXM_REDIS_TEST_STREAM"), redis_conn=conn, **kwargs):
        self.stream_name, self.redis_conn = stream_name, redis_conn
        self.strm = stream.ThreeJsSharedDict(self.stream_name, self.redis_conn)

        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

        self._lines = generate_three_lines((self.points_a, self.points_b),
                                           colors=(ColorRGB(255, 100, 0).decimal, ColorRGB(100, 255, 0).decimal))
        self.part = self._points_a["part"]
        # print(self.params)
        self._solved = solve(**self.params)(MyLine)

        # print(self._solved)
        self._axis = generate_three_axis(self._solved, ColorRGB(200, 200, 200).decimal)
        self._root = copy.deepcopy(self._lines)
        merge_groups(self._root, self._axis)

        self._root["object"]["uuid"] = self.uuid
        self.strm |= self._root

        return self


grd = MFBGrid(
    points_a={
        "points": ["A", "B", "C", "D"],
        "part": "SW"
    },
    points_b={
        "points": ["A", "D"],
        "part": "SW"
    }
)
grd.strm.commit()


@strawberry.type
class Query:
    @strawberry.field
    def grid(self) -> Grid:
        return Grid(grd)

    @strawberry.field
    def geometry_by_uuid(self, uuid: str) -> Geometry:
        es = ElementSequence(grd._root["geometries"])
        # print(es)
        return Geometry(**es.get_from_index(es.search_from_key_value("uuid", uuid)))

    @strawberry.field
    def all(self) -> JSON:
        return grd._root

    @strawberry.field
    def lines(self) -> JSON:
        return [{"a": ln.a, "b": ln.b} for ln in grd._solved]


#

#    @strawberry.field
#    @property
#    def object3d(self) -> JSON:
#        return generate_three_lines(ElementSequence(self.lines)["points"],
#                                    colors=(ColorRGB(255, 100, 0).decimal, ColorRGB(100, 255, 0).decimal))
#
# @strawberry.field
# def axis(self, points: list[str], part: MFBPart = MFBPart.SW) -> list(BaseAxis):
#    return list(map(lambda x, y: BaseAxis(points=x,part=y), zip(points,part)))

# prm_a = 0.0
# prm_b = 0.0
# h = 600.0
# 0.042
# 0.008

@strawberry.type
class Mutation:
    @strawberry.field
    def grid(self, axis_a: BaseAxis = BaseAxis(**{
        "points": ["A", "B", "C", "D"],
        "part": "SW"
    }),
             axis_b: BaseAxis = BaseAxis(**{
                 "points": ["A", "D"],
                 "part": "SW"
             })) -> Grid:
        global param_stream
        grd(**dict(
            points_a=axis_a.todict(),
            points_b=axis_b.todict(), t0=t0,
            t1=t1,
            h=h
        ))
        param_stream.commit()
        grd.strm.commit()

        return Grid(grd)


schema = strawberry.Schema(query=Query, mutation=Mutation, types=(MFBPart, Grid, BasePoint, Point, BaseAxis, Line))

graphql_app = GraphQLRouter(schema)
from fastapi import FastAPI
import uvicorn

grid_app = FastAPI()
grid_app.include_router(graphql_app, prefix="/graphql")
app = FastAPI()

from fastapi.responses import RedirectResponse
@grid_app.get("/")
def home():
    return RedirectResponse(os.getenv("CXM_VIEWER_SCENE"))


app.mount("/cxm/api/v2/mfb_grid", grid_app)
if __name__ == "__main__":
    print(os.getenv("CXM_VIEWER_SCENE"))
    uvicorn.run("main:app", host="0.0.0.0", port=5777, reload=False)
