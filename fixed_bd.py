import yaml
from hypnotoad import tokamak
from hypnotoad.core.mesh import BoutMesh
with open("/home/pcphp/coding_work/gfile/gfile.eqdsk",'r') as gf:
  eq=tokamak.read_geqdsk(gf)


filename = "fixed_bd.yaml"
with open(filename, "r") as inputfile:
        options = yaml.safe_load(inputfile)
mesh = BoutMesh(eq,options)
mesh.geometry()
mesh.writeGridfile("bout.grd.nc")