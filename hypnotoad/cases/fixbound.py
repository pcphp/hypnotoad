# Generate grids for tokamak configurations
#

import numpy as np
from optionsfactory import WithMeta
from optionsfactory.checks import (
    is_non_negative,
    is_positive,
    NoneType,
)
from scipy import interpolate
from scipy.integrate import solve_ivp
import warnings
from collections import OrderedDict

from ..core.equilibrium import Equilibrium, EquilibriumRegion, Point2D

from ..utils import critical, polygons
from ..utils.utils import with_default


class FixedBdEquilibrium(Equilibrium):
    """
    Axisymmetric tokamak equilibrium

    Implements :class:`Equilibrium <hypnotoad.core.equilibrium.Equilibrium>`.

    Finds the central O-point of the equilibrium, and the X-points. Creates
    :class:`EquilibriumRegion <hypnotoad.core.equilibrium.EquilibriumRegion>` objects
    for the core (separate outer and inner for double null configurations) and divertor
    legs.
    """

    # Tokamak-specific options and default values
    user_options_factory = Equilibrium.user_options_factory.add(
        reverse_current=WithMeta(
            False,
            doc="Reverse the sign of the poloidal field",
            value_type=bool,
        ),
        psi_divide_twopi=WithMeta(
            False,
            doc="Divide poloidal flux, and so poloidal field, by 2pi",
            value_type=bool,
        ),
        nx_core=WithMeta(
            68,
            doc="Number of radial points in the core",
            value_type=int,
            check_all=is_positive,
        ),
    
        psinorm_core=WithMeta(
            0.9,
            doc="Normalised psi of the inner radial (core) boundary",
            value_type=[float, int],
        ),
        psinorm_sol=WithMeta(
            1.1,
            doc="Normalised psi of the outer radial (SOL) boundary",
            value_type=[float, int],
        ),
        
        # Poloidal flux ranges.
        # These are the values which are used in the mesh generation
        # The default values comes from the psinorm values, but the user
        # can override these defaults.
        psi_core=WithMeta(
            None,
            doc=(
                "Unnormalised poloidal flux value at the core boundary, used in mesh "
                "generation. Overrides psinorm_core if this value is given, if the "
                "option is none, then calculated from psinorm_core"
            ),
            value_type=[float, int, NoneType],
        ),
        psi_sol=WithMeta(
            None,
            doc=(
                "Unnormalised poloidal flux value at the SOL boundary, used in mesh "
                "generation. Overrides psinorm_sol if this value is given, if the "
                "option is none, then calculated from psinorm_sol"
            ),
            value_type=[float, int, NoneType],
        ),
        
        reverse_Bt=WithMeta(
            False,
            doc="Reverse the sign of toroidal magnetic field Bt.",
            value_type=bool,
        ),
        
        # Tolerance for positioning points that should be at X-point, but need to be
        # slightly displaced from the null so code can follow Grad(psi).
        # Number between 0. and 1.
        
        
    )

    def __init__(
        self,
        R1D,
        Z1D,
        psi2D,
        psi1D,
        fpol1D,
        pressure=None,
        wall=None,
        psi_axis_gfile=None,
        psi_bdry_gfile=None,
        make_regions=True,
        settings=None,
        nonorthogonal_settings=None,
    ):
        """
        Create a Tokamak equilibrium.

        Inputs
        ------

        R1D[nx]       1D array of major radius [m]
        Z1D[ny]       1D array of height [m]
        psi2D[nx,ny]  2D array of poloidal flux [Wb]
        psi1D[nf]     1D array of poloidal flux [Wb]
        fpol1D[nf]    1D array of f=R*Bt [mT]

        Keywords
        --------

        pressure[nf] = 1D array of pressure as a function of psi1D [Pa]

        wall = [(R0,Z0), (R1, Z1), ...]
               A list of coordinate pairs, defining the vessel wall.
               The wall is closed, so the last point connects to the first.
        psi_axis_gfile = float
               The value of poloidal flux on the magnetic axis, given by the EFIT file.
               self.psi_axis is the value calculated on the O-point.
        psi_bdry_gfile = float
               The value of poloidal flux at the plasma boundary, given by the EFIT file.
               self.psi_bdry is the value calculated on the X-point.
        make_regions = bool
               Generate the regions to be meshed. The default (True)
               means that the object is complete after initialisation.
               If set to False, e.g. for testing, self.makeRegions() should
               be called to generate the regions.
        settings = A dict that will be used to set non-default values of options
               (self.user_options)
        nonorthogonal_settings = A dict that will be used to set non-default values of
               options (self.nonorthogonal_options)

        """
        self.psi_axis=psi_axis_gfile
        self.user_options = self.user_options_factory.create(settings)

        if self.user_options.reverse_current:
            warnings.warn("Reversing the sign of the poloidal field")
            psi2D *= -1.0
            psi1D *= -1.0

        if self.user_options.psi_divide_twopi:
            warnings.warn("Dividing poloidal flux by 2pi")
            twopi = 2 * np.pi
            psi2D /= twopi
            psi1D /= twopi
            if psi_axis_gfile is not None:
                psi_axis_gfile /= twopi
            if psi_bdry_gfile is not None:
                psi_bdry_gfile /= twopi

        if self.user_options.reverse_Bt:
            warnings.warn("Reversing the sign of the toroidal field")
            fpol1D *= -1.0

        self.psi_increasing = psi1D[-1] > psi1D[0]
            # Extend the array to outer-most psi on grid
            
        self.magneticFunctionsFromGrid(
            R1D, Z1D, psi2D, self.user_options.psi_interpolation_method
        )

        self.f_psi_sign = 1.0
        if len(fpol1D) > 0:
            # Spline for interpolation of f = R*Bt

            # Note: psi1D must be increasing
            if psi1D[-1] < psi1D[0]:
                self.f_psi_sign = -1.0

            self.f_spl = interpolate.InterpolatedUnivariateSpline(
                psi1D * self.f_psi_sign, fpol1D, ext=3
            )
            # ext=3 specifies that boundary values are used outside range

            # Spline representing the derivative of f
            self.fprime_spl = self.f_spl.derivative()
        else:
            self.f_spl = lambda psi: 0.0
            self.fprime_spl = lambda psi: 0.0

        # Optional pressure profile
        if pressure is not None:
            self.p_spl = interpolate.InterpolatedUnivariateSpline(
                psi1D * self.f_psi_sign, pressure, ext=3
            )
        else:
            # If no pressure, then not output to grid file
            self.p_spl = None

        # Find critical points (O- and X-points)
        R2D, Z2D = np.meshgrid(R1D, Z1D, indexing="ij")
             

        self.psi_sep = [psi_bdry_gfile,psi_bdry_gfile+0.001]

        # Bounding box for domain
        self.Rmin = min(R1D)
        self.Rmax = max(R1D)
        self.Zmin = min(Z1D)
        self.Zmax = max(Z1D)

        # Wall geometry. Note: should be anti-clockwise
        if wall is None:
            # No wall given, so add one which is just inside the domain edge
            offset = 1e-2  # in m
            wall = [
                (self.Rmin + offset, self.Zmin + offset),
                (self.Rmax - offset, self.Zmin + offset),
                (self.Rmax - offset, self.Zmax - offset),
                (self.Rmin + offset, self.Zmax - offset),
            ]
        elif len(wall) < 3:
            raise ValueError(
                f"Wall must be a polygon, so should have at least 3 points. Got "
                f"wall={wall}"
            )

        if polygons.clockwise(wall):
            wall = wall[
                ::-1
            ]  # Reverse, without modifying input list (which .reverse() would)
        self.wall = [Point2D(r, z) for r, z in wall]

        self.equilibOptions = {}

        super().__init__(nonorthogonal_settings)

        # Print the table of options
        print(self.user_options.as_table(), flush=True)
        if not self.user_options.orthogonal:
            print(self.nonorthogonal_options.as_table(), flush=True)

        if make_regions:
            # Create self.regions
            self.makeRegions()


    # psi values
        
    def _psinorm_to_psi(self, psinorm):
        if psinorm is None:
            return None
        return self.psi_axis + psinorm * (self.psi_sep[0] - self.psi_axis)

    def _psi_to_psinorm(self, psi):
        if psi is None:
            return None
        return (psi - self.psi_axis) / (self.psi_sep[0] - self.psi_axis)

    def makeRegions(self):
        """Main region generation function. Regions are logically
        rectangular ranges in poloidal angle; segments are
        ranges of poloidal flux (radial coordinate). Poloidal ranges,
        radial segments, and the connections between them describe
        the topology and geometry of the mesh.

        This function is called by __init__ to generate regions unless
        make_regions is set to False.

        The main steps in doing this are:

        1. Set defaults if not already set by user
        2. Identify whether single or double null
        3. Describe the leg and core regions, depending on the topology
        4. Follow flux surfaces based on core region descriptions
           (self.coreRegionToRegion)
        5. Process all regions into a set of EquilibriumObjects
           (self.createRegionObjects)
        6. Sort the EquilibriumRegion objects for BoutMesh output
           (self.createRegionObjects).
        7. Connect regions together

        Modifies:

        * self.user_options - Sets default values if not set by user
        * self.regions - OrderedDict of EquilibriumRegion objects

        """
        if self.psi_axis is None:
            raise ValueError("psi_axis has not been set")

        self.psi_core = with_default(
            self.user_options.psi_core,
            self._psinorm_to_psi(self.user_options.psinorm_core),
        )

      
       
        self.regions = self.createRegionObjects(all_regions, segments)

   
        """
        Create the specifications for a single null configuration

        Returns
        -------

        leg_regions    Dictionary describing poloidal regions in legs
        core_regions   Dictionary describing poloidal regions between X-points
        segments       Dictionary describing radial segments
                        nx          Number of radial (x) cells
                        psi_vals    1D array of poloidal flux values. Length 2*nx+1
        connections    List of connections between regions
        """
    


    def coreRegionToRegion(self, core_regions, npoints=100):
        """
        For each poloidal arc along a separatrix between two X-points
        (core region), find a set of points between the X-points.
        The result is returned as a dict of regions (like leg regions)

        Parameters
        ----------
        core_regions : dict
            A dictionary containing definitions of core regions.
            Keys are:

              * segments - A list of segment names
              * ny - Number of poloidal (y) points
              * kind - A string e.g. "wall.X"
              * xpoints_at_start - A list of Point2D objects or None
              * xpoints_at_end - A list of Point2D objects or None
              * psi_at_start - Poloidal flux at the start of the line
              * psi_at_end - Poloidal flux at the end of the line

        npoints : int
            number of points in each core region

        Returns
        -------
        A dictionary of region definitions, compatible with processing code
        for leg regions.
        """

        # Loop through core regions, calculate points along the lines,
        # and put into the result dictionary
        result = {}
        for name, region in core_regions.items():
            region = region.copy()  # So we don't modify the input

            def any_value(values):
                "Return the first non-None value in list, or None"
                return next((val for val in values if val is not None), None)  # Default

            start_x = any_value(region["xpoints_at_start"])
            end_x = any_value(region["xpoints_at_end"])
            start_psi = region["psi_at_start"]
            end_psi = region["psi_at_end"]

            # Range of angles. Note: This angle goes anticlockwise
            # so core regions need to be reversed
            start_angle = np.arctan2(
                start_x.Z - self.o_point.Z, start_x.R - self.o_point.R
            )
            end_angle = np.arctan2(end_x.Z - self.o_point.Z, end_x.R - self.o_point.R)
            if end_angle >= start_angle:
                end_angle -= 2 * np.pi

            # Angle offset from the X-point. This is to reduce the chances
            # of missing the X-point, passing through to the other side.
            dtheta = 0.5 * (end_angle - start_angle) / npoints
            r0, z0 = self.o_point.R, self.o_point.Z  # Location of O-point

            # If the start and end X-point are different, interpolate
            # from one to the other. This helps ensure that constructed
            # coordinate lines don't go the wrong side of X-points.
            def psival(angle):
                "Interpolation in psi with angle"
                norm = (angle - start_angle) / (end_angle - start_angle)

                # Smoother step function (Ken Perlin)
                # https://en.wikipedia.org/wiki/Smoothstep
                norm = 6.0 * norm**5 - 15.0 * norm**4 + 10.0 * norm**3

                return norm * end_psi + (1.0 - norm) * start_psi

            # Iterate in angle from start to end
            points = [
                Point2D(
                    *critical.find_psisurface(
                        self,
                        r0,
                        z0,
                        r0 + 8.0 * np.cos(angle),
                        z0 + 8.0 * np.sin(angle),
                        psival=psival(angle),
                    )
                )
                for angle in np.linspace(
                    start_angle + dtheta, end_angle - dtheta, npoints
                )
            ]

            # Add points to the beginning and end near (but not at) the X-points
            diff = self.user_options.xpoint_offset
            if diff < 0.0 or diff > 1.0:
                raise ValueError(f"xpoint_offset={diff} should be between 0 and 1.")

            region["points"] = (
                [(1.0 - diff) * start_x + diff * points[0]]
                + points
                + [(1.0 - diff) * end_x + diff * points[-1]]
            )

            region["psi"] = None  # Not all points on the same flux surface

            result[name] = region
        return result

    def segmentsWithPsivals(self, segments):
        """
        Grids radial segments

        Parameters
        ----------

        segments : dict
            A dict of segments, each of which is a dictionary containing:

              * nx - Number of points in psi (x)
              * psi_start - The poloidal flux at the start of the segment
              * psi_end - The poloidal flux at the end of the segment
              * grad_start - [optional]  Cell spacing at the start
              * grad_end - [optional] Cell spacing at the end

        The input is not modified

        Returns
        -------

        A dictionary of segments, with an additional key "psi_vals"
        """
        result = {}
        for name, segment in segments.items():
            segment_with_psival = segment.copy()

            psi_func = self.getSmoothMonotonicGridFunc(
                segment["nx"],
                segment["psi_start"],
                segment["psi_end"],
                grad_lower=segment.get("grad_start", None),
                grad_upper=segment.get("grad_end", None),
            )

            segment_with_psival["psi_vals"] = self.make1dGrid(segment["nx"], psi_func)
            result[name] = segment_with_psival
        return result

    def createRegionObjects(self, all_regions, segments):
        """
        Create an OrderedDict of EquilibriumRegion objects,
        using specifications for the regions and segments
        in the all_regions and segments dictionaries.

        These regions need to be sorted so that BoutMesh
        can generate branch cut indices. To do this ordering,
        a limited set of region names should be used:
        - 'inner_lower_divertor'
        - 'core' (for single null)
        - 'inner_core' and 'outer_core' (for double null)
        - 'inner_upper_divertor'
        - 'outer_upper_divertor'
        - 'outer_lower_divertor'

        Parameters
        ----------

        all_regions : dict
            Dictionary containing specification for each region
        segments : dict
            Dictionary of radial segment definitions
            Keys are:

              * nx - Number of radial cells
              * psi_vals - 1D array of psi values, length 2*nx+1

        Returns
        -------

        None. Modifies self.regions
        """

        # Set the total number of grid cells in y
        self.ny_total = sum([region["ny"] for region in all_regions.values()])

        # Loop through all regions. For each one create an EquilibriumRegion
        region_objects = {}
        for name, region in all_regions.items():
            eqreg = EquilibriumRegion(
                equilibrium=self,
                name=name,
                nSegments=len(region["segments"]),  # The number of radial regions
                nx=[segments[seg_name]["nx"] for seg_name in region["segments"]],
                ny=region["ny"],
                ny_total=self.ny_total,
                kind=region["kind"],
                # The following arguments are passed through to PsiContour
                points=region["points"],  # list of Point2D objects on the line
                psival=region["psi"],
                Rrange=(self.Rmin, self.Rmax),
                Zrange=(self.Zmin, self.Zmax),
            )

            # Grids of psi values in each segment
            eqreg.psi_vals = [segments[name]["psi_vals"] for name in region["segments"]]

            eqreg.separatrix_radial_index = 1

            if "xpoints_at_start" in region:
                eqreg.xPointsAtStart = region["xpoints_at_start"]

            if "xpoints_at_end" in region:
                eqreg.xPointsAtEnd = region["xpoints_at_end"]

            if "wall_at_start" in region:
                eqreg.wallSurfaceAtStart = region["wall_at_start"]

            if "wall_at_end" in region:
                eqreg.wallSurfaceAtEnd = region["wall_at_end"]

            # Pressure profiles
            if self.p_spl is not None:
                if "wall" in region["kind"]:
                    # A leg region. Reflect the pressure in poloidal flux
                    # so that the pressure in the private flux region falls
                    # away from the separatrix

                    # Determine if poloidal flux is increasing or decreasing with radius
                    sign = np.sign(self.psi_sep[0] - self.psi_axis)

                    if region["psi"] is None:
                        raise ValueError("No psi values in region")
                    leg_psi = region["psi"]
                    eqreg.pressure = lambda psi: self.pressure(
                        leg_psi + sign * abs(psi - leg_psi)
                    )
                else:
                    # Core region, so use the core pressure
                    eqreg.pressure = self.pressure

            region_objects[name] = eqreg
        # The region objects need to be sorted, so that the
        # BoutMesh generator can use jyseps indices to introduce branch cuts

        if "inner_lower_divertor" in region_objects:
            if not self.user_options.start_at_upper_outer:
                ordering = [
                    "inner_lower_divertor",
                    # For single null; in double null this will be ignored
                    "core",
                    # For double null; in single null these will be ignored
                    "inner_core",
                    "inner_upper_divertor",
                    "outer_upper_divertor",
                    "outer_core",
                    #
                    "outer_lower_divertor",
                ]
            else:
                # Special case intended for backward compatibility with simulations
                # using upper-disconnected-double-null IDL-hypnotoad grid files
                ordering = [
                    "outer_upper_divertor",
                    "outer_core",
                    "outer_lower_divertor",
                    "inner_lower_divertor",
                    "core",
                    "inner_core",
                    "inner_upper_divertor",
                ]
        else:
            # Upper single null special case
            ordering = ["outer_upper_divertor", "core", "inner_upper_divertor"]

        # Check that all regions are in the ordering
        for key in region_objects:
            if key not in ordering:
                raise ValueError("Region '" + key + "' is not in ordering")

        # Sort the region objects, ignoring regions which are not present
        return OrderedDict(
            [(key, region_objects[key]) for key in ordering if key in region_objects]
        )

    @Equilibrium.handleMultiLocationArray
    def fpol(self, psi):
        """poloidal current function,
        returns fpol such that B_toroidal = fpol/R"""
        return self.f_spl(psi * self.f_psi_sign)

    @Equilibrium.handleMultiLocationArray
    def fpolprime(self, psi):
        """psi-derivative of fpol"""
        return self.fprime_spl(psi * self.f_psi_sign)

    @Equilibrium.handleMultiLocationArray
    def pressure(self, psi):
        """Plasma pressure in Pascals"""
        if self.p_spl is None:
            return None
        return self.p_spl(psi * self.f_psi_sign)

    @property
    def Bt_axis(self):
        """Calculate toroidal field on axis"""
        return self.fpol(self.psi_axis) / self.o_point.R


def read_geqdsk(
    filehandle, settings=None, nonorthogonal_settings=None, make_regions=True
):
    """
    Read geqdsk formatted data from a file object, returning
    a TokamakEquilibrium object

    Parameters
    ----------
    filehandle : file handle
        A file handle to read
    settings : dict
        dict passed to TokamakEquilibrium
    nonorthogonal_settings : dict
        dict passed to TokamakEquilibrium

    Options used:

    * ``reverse_current = bool`` - Changes the sign of poloidal flux psi
    * ``extrapolate_profiles = bool`` - Extrapolate pressure using exponential
    * ``psi_divide_twopi = bool`` - Divide poloidal flux, and so poloidal field, by 2pi
    """

    if settings is None:
        settings = {}

    from ..geqdsk._geqdsk import read as geq_read

    data = geq_read(filehandle)

    # Range of psi normalises psi derivatives
    psi_bdry_gfile = data["sibdry"]
    psi_axis_gfile = data["simagx"]

    # 1D grid on which fpol is defined. Goes from normalised psi 0 to 1
    psi1D = np.linspace(psi_axis_gfile, psi_bdry_gfile, data["nx"], endpoint=True)

    R1D = np.linspace(
        data["rleft"], data["rleft"] + data["rdim"], data["nx"], endpoint=True
    )

    Z1D = np.linspace(
        data["zmid"] - 0.5 * data["zdim"],
        data["zmid"] + 0.5 * data["zdim"],
        data["ny"],
        endpoint=True,
    )

    psi2D = data["psi"]

    # Get the wall
    if "rlim" in data and "zlim" in data:
        wall = list(zip(data["rlim"], data["zlim"]))
    else:
        wall = None

    pressure = data["pres"]
    fpol = data["fpol"]

    result = FixedBdEquilibrium(
        R1D,
        Z1D,
        psi2D,
        psi1D,
        fpol,
        psi_bdry_gfile=psi_bdry_gfile,
        psi_axis_gfile=psi_axis_gfile,
        pressure=pressure,
        wall=wall,
        make_regions=make_regions,
        settings=settings,
        nonorthogonal_settings=nonorthogonal_settings,
    )

    # Store geqdsk input as a string in the TokamakEquilibrium object so we can save it
    # in BoutMesh.writeGridFile
    # reset to beginning of file
    filehandle.seek(0)
    # read file as a single string and store in result
    result.geqdsk_input = filehandle.read()
    # also save filename, if it exists
    if hasattr(filehandle, "name"):
        result.geqdsk_filename = filehandle.name

    return result
