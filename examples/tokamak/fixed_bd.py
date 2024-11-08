# Generate grids for tokamak configurations without Xpoints or limiter configures
#
import sys
sys.path.append('/home/pcphp/coding_work/hypnotoad/')
import yaml
from hypnotoad import tokamak, fixbound
from hypnotoad.core.mesh import BoutMesh
from hypnotoad.geqdsk._geqdsk import read as geq_read

with open("/home/pcphp/coding_work/gfile/gfile.eqdsk",'r') as gf:
    eq=fixbound.read_geqdsk(gf)
    # data = geq_read(gf)

filename = "fixed_bd.yaml"
with open(filename, "r") as inputfile:
        options = yaml.safe_load(inputfile)
mesh = BoutMesh(eq,options)
# mesh.geometry()
# mesh.writeGridfile("bout.grd.nc")