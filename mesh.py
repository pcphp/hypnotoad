"""
Classes to handle Meshes and geometrical quantities for generating BOUT++ grids
"""

from copy import deepcopy
import numbers
import re
import warnings

import numpy
from scipy.integrate import solve_ivp

from boututils.boutarray import BoutArray

from .equilibrium import calc_distance, Point2D, FineContour

class MultiLocationArray(numpy.lib.mixins.NDArrayOperatorsMixin):
    """
    Container for arrays representing points at different cell locations
    Not all have to be filled.
    """
    _centre_array = None
    _xlow_array = None
    _ylow_array = None
    _corners_array = None

    def __init__(self, nx, ny):
        self.nx = nx
        self.ny = ny
        # Attributes that will be saved to output files along with the array
        self.attributes = {}

    @property
    def centre(self):
        if self._centre_array is None:
            self._centre_array = numpy.zeros([self.nx, self.ny])
        return self._centre_array

    @centre.setter
    def centre(self, value):
        if self._centre_array is None:
            self._centre_array = numpy.zeros([self.nx, self.ny])
        self._centre_array[...] = value

    @property
    def xlow(self):
        if self._xlow_array is None:
            self._xlow_array = numpy.zeros([self.nx + 1, self.ny])
        return self._xlow_array

    @xlow.setter
    def xlow(self, value):
        if self._xlow_array is None:
            self._xlow_array = numpy.zeros([self.nx + 1, self.ny])
        self._xlow_array[...] = value

    @property
    def ylow(self):
        if self._ylow_array is None:
            self._ylow_array = numpy.zeros([self.nx, self.ny + 1])
        return self._ylow_array

    @ylow.setter
    def ylow(self, value):
        if self._ylow_array is None:
            self._ylow_array = numpy.zeros([self.nx, self.ny + 1])
        self._ylow_array[...] = value

    @property
    def corners(self):
        if self._corners_array is None:
            self._corners_array = numpy.zeros([self.nx + 1, self.ny + 1])
        return self._corners_array

    @corners.setter
    def corners(self, value):
        if self._corners_array is None:
            self._corners_array = numpy.zeros([self.nx + 1, self.ny + 1])
        self._corners_array[...] = value

    # The following __array_ufunc__ implementation allows the MultiLocationArray class to
    # be handled by Numpy functions, and add, subtract, etc. like an ndarray.
    # The implementation is mostly copied from the example in
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.lib.mixins.NDArrayOperatorsMixin.html#numpy.lib.mixins.NDArrayOperatorsMixin

    # One might also consider adding the built-in list type to this
    # list, to support operations like np.add(array_like, list)
    _HANDLED_TYPES = (numpy.ndarray, numbers.Number)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        out = kwargs.get('out', ())
        for x in inputs + out:
            # Only support operations with instances of _HANDLED_TYPES.
            # Use MultiLocationArray instead of type(self) for isinstance to
            # allow subclasses that don't override __array_ufunc__ to
            # handle MultiLocationArray objects.
            if not isinstance(x, self._HANDLED_TYPES + (MultiLocationArray,)):
                return NotImplemented

        result = MultiLocationArray(self.nx, self.ny)

        # Defer to the implementation of the ufunc on unwrapped values.
        if self._centre_array is not None:
            this_inputs = tuple(x._centre_array if isinstance(x, MultiLocationArray)
                    else x for x in inputs)
            if out:
                kwargs['out'] = tuple(
                    x.centre if isinstance(x, MultiLocationArray) else x
                    for x in out)
            this_result = getattr(ufunc, method)(*this_inputs, **kwargs)

            if type(this_result) is tuple:
                # multiple return values
                if not type(result) is tuple:
                    result = tuple(MultiLocationArray(self.nx, self.ny)
                            for x in this_result)
                for i,x in enumerate(this_result):
                    result[i].centre = x

            elif method == 'at':
                # no return value
                result = None
            else:
                # one return value
                result.centre = this_result

        # Defer to the implementation of the ufunc on unwrapped values.
        if self._xlow_array is not None:
            this_inputs = tuple(x._xlow_array if isinstance(x, MultiLocationArray)
                    else x for x in inputs)
            if out:
                kwargs['out'] = tuple(
                    x.xlow if isinstance(x, MultiLocationArray) else x
                    for x in out)
            this_result = getattr(ufunc, method)(*this_inputs, **kwargs)

            if type(this_result) is tuple:
                # multiple return values
                if not type(result) is tuple:
                    result = tuple(MultiLocationArray(self.nx, self.ny)
                            for x in this_result)
                for i,x in enumerate(this_result):
                    result[i].xlow = x

            elif method == 'at':
                # no return value
                result = None
            else:
                # one return value
                result.xlow = this_result

        # Defer to the implementation of the ufunc on unwrapped values.
        if self._ylow_array is not None:
            this_inputs = tuple(x._ylow_array if isinstance(x, MultiLocationArray)
                    else x for x in inputs)
            if out:
                kwargs['out'] = tuple(
                    x.ylow if isinstance(x, MultiLocationArray) else x
                    for x in out)
            this_result = getattr(ufunc, method)(*this_inputs, **kwargs)

            if type(this_result) is tuple:
                # multiple return values
                if not type(result) is tuple:
                    result = tuple(MultiLocationArray(self.nx, self.ny)
                            for x in this_result)
                for i,x in enumerate(this_result):
                    result[i].ylow = x

            elif method == 'at':
                # no return value
                result = None
            else:
                # one return value
                result.ylow = this_result

        # Defer to the implementation of the ufunc on unwrapped values.
        if self._corners_array is not None:
            this_inputs = tuple(x._corners_array if isinstance(x, MultiLocationArray)
                    else x for x in inputs)
            if out:
                kwargs['out'] = tuple(
                    x.corners if isinstance(x, MultiLocationArray) else x
                    for x in out)
            this_result = getattr(ufunc, method)(*this_inputs, **kwargs)

            if type(this_result) is tuple:
                # multiple return values
                if not type(result) is tuple:
                    result = tuple(MultiLocationArray(self.nx, self.ny)
                            for x in this_result)
                for i,x in enumerate(this_result):
                    result[i].corners = x

            elif method == 'at':
                # no return value
                result = None
            else:
                # one return value
                result.corners = this_result

        return result

    def zero(self):
        # Initialise all locations, set them to zero and return the result
        self.centre = 0.
        self.xlow = 0.
        self.ylow = 0.
        self.corners = 0.
        return self

class MeshRegion:
    """
    A simple rectangular region of a Mesh, that connects to one other region (or has a
    boundary) on each edge.
    Note that these regions include cell face and boundary points, so there are
    (2nx+1)*(2ny+1) points for an nx*ny grid.
    """
    def __init__(self, meshParent, myID, equilibriumRegion, connections, radialIndex):
        self.name = equilibriumRegion.name+'('+str(radialIndex)+')'
        print('creating region', myID, '-', self.name)

        # the Mesh object that owns this MeshRegion
        self.meshParent = meshParent

        # ID that Mesh uses to keep track of its MeshRegions
        self.myID = myID

        # EquilibriumRegion representing the segment associated with this region
        self.equilibriumRegion = equilibriumRegion.copy()

        self.user_options = self.equilibriumRegion.user_options
        self.options = self.equilibriumRegion.options

        # sizes of the grid in this MeshRegion, include boundary guard cells
        self.nx = self.options.nx[radialIndex]
        self.ny = self.equilibriumRegion.ny(radialIndex)
        self.ny_noguards = self.equilibriumRegion.ny_noguards

        # psi values for radial grid
        self.psi_vals = numpy.array(self.equilibriumRegion.psi_vals[radialIndex])
        assert len(self.psi_vals) == 2*self.nx + 1, 'should be a psi value for each radial point'

        # Dictionary that specifies whether a boundary is connected to another region or
        # is an actual boundary
        self.connections = connections

        # Number of this region, counting radially outward
        self.radialIndex = radialIndex

        # Number of this region in its y-group
        self.yGroupIndex = None

        # Absolute tolerance for checking if two points are the same
        self.atol = 1.e-7

        # get points in this region
        self.contours = []
        if self.radialIndex < self.equilibriumRegion.separatrix_radial_index:
            # region is inside separatrix, so need to follow line from the last psi_val to
            # the first
            temp_psi_vals = self.psi_vals[::-1]
        else:
            temp_psi_vals = self.psi_vals

        # set sign of step in psi towards this region from primary separatrix
        if temp_psi_vals[-1] - self.equilibriumRegion.psival > 0:
            psi_sep_plus_delta = self.equilibriumRegion.psival + self.user_options.poloidal_spacing_delta_psi
        else:
            psi_sep_plus_delta = self.equilibriumRegion.psival - self.user_options.poloidal_spacing_delta_psi

        # Make vector along grad(psi) at start of equilibriumRegion
        vec_points = followPerpendicular(
                self.meshParent.equilibrium.f_R, self.meshParent.equilibrium.f_Z,
                self.equilibriumRegion[self.equilibriumRegion.startInd],
                self.equilibriumRegion.psival,
                [self.equilibriumRegion.psival, psi_sep_plus_delta],
                rtol=self.user_options.follow_perpendicular_rtol,
                atol=self.user_options.follow_perpendicular_atol)
        self.equilibriumRegion.gradPsiSurfaceAtStart = (vec_points[1].as_ndarray() - vec_points[0].as_ndarray())
        # Make vector along grad(psi) at end of equilibriumRegion
        vec_points = followPerpendicular(
                self.meshParent.equilibrium.f_R, self.meshParent.equilibrium.f_Z,
                self.equilibriumRegion[self.equilibriumRegion.endInd],
                self.equilibriumRegion.psival,
                [self.equilibriumRegion.psival, psi_sep_plus_delta],
                rtol=self.user_options.follow_perpendicular_rtol,
                atol=self.user_options.follow_perpendicular_atol)
        self.equilibriumRegion.gradPsiSurfaceAtEnd = (vec_points[1].as_ndarray() - vec_points[0].as_ndarray())

        # Calculate the perp_d_lower/perp_d_upper corresponding to d_lower/d_upper on the
        # separatrix contour
        # Use self.equilibriumRegion.fine_contour for the vector along the separatrix
        # because then the vector will not change when the grid resolution changes
        if self.equilibriumRegion.wallSurfaceAtStart is None:
            # lower end
            unit_vec_separatrix = (
                    self.equilibriumRegion.fine_contour.positions[
                        self.equilibriumRegion.fine_contour.startInd + 1, :]
                    - self.equilibriumRegion.fine_contour.positions[
                        self.equilibriumRegion.fine_contour.startInd, :])
            unit_vec_separatrix /= numpy.sqrt(numpy.sum(unit_vec_separatrix**2))
            unit_vec_surface = self.equilibriumRegion.gradPsiSurfaceAtStart
            unit_vec_surface /= numpy.sqrt(numpy.sum(unit_vec_surface**2))
            cos_angle = numpy.sum(unit_vec_separatrix*unit_vec_surface)
            # this gives abs(sin_angle), but that's OK because we only want the magnitude to
            # calculate perp_d
            sin_angle = numpy.sqrt(1. - cos_angle**2)
            self.options.set(perp_d_lower=self.options.polynomial_d_lower * sin_angle)
        if self.equilibriumRegion.wallSurfaceAtEnd is None:
            # upper end
            unit_vec_separatrix = (
                    self.equilibriumRegion.fine_contour.positions[
                        self.equilibriumRegion.fine_contour.endInd - 1, :]
                    - self.equilibriumRegion.fine_contour.positions[
                        self.equilibriumRegion.fine_contour.endInd, :])
            unit_vec_separatrix /= numpy.sqrt(numpy.sum(unit_vec_separatrix**2))
            unit_vec_surface = self.equilibriumRegion.gradPsiSurfaceAtEnd
            unit_vec_surface /= numpy.sqrt(numpy.sum(unit_vec_surface**2))
            cos_angle = numpy.sum(unit_vec_separatrix*unit_vec_surface)
            # this gives abs(sin_angle), but that's OK because we only want the magnitude to
            # calculate perp_d
            sin_angle = numpy.sqrt(1. - cos_angle**2)
            self.options.set(perp_d_upper=self.options.polynomial_d_upper * sin_angle)

        print('Following perpendicular: ' + str(1) + '/'
                + str(len(self.equilibriumRegion)), end='\r')
        perp_points = followPerpendicular(self.meshParent.equilibrium.f_R,
                self.meshParent.equilibrium.f_Z, self.equilibriumRegion[0],
                self.equilibriumRegion.psival, temp_psi_vals,
                rtol=self.user_options.follow_perpendicular_rtol,
                atol=self.user_options.follow_perpendicular_atol)
        if self.radialIndex < self.equilibriumRegion.separatrix_radial_index:
            # region is inside separatrix, so points were found from last to first
            perp_points.reverse()
        for i,point in enumerate(perp_points):
            self.contours.append(self.equilibriumRegion.newContourFromSelf(points=[point],
                psival=self.psi_vals[i]))
            self.contours[i].global_xind = self.globalXInd(i)
        for i,p in enumerate(self.equilibriumRegion[1:]):
            print('Following perpendicular: ' + str(i+2) + '/'
                    + str(len(self.equilibriumRegion)), end='\r')
            perp_points = followPerpendicular(self.meshParent.equilibrium.f_R,
                    self.meshParent.equilibrium.f_Z, p,
                    self.equilibriumRegion.psival, temp_psi_vals,
                    rtol=self.user_options.follow_perpendicular_rtol,
                    atol=self.user_options.follow_perpendicular_atol)
            if self.radialIndex < self.equilibriumRegion.separatrix_radial_index:
                perp_points.reverse()
            for j,point in enumerate(perp_points):
                self.contours[j].append(point)

        # refine the contours to make sure they are at exactly the right psi-value
        for contour in self.contours:
            contour.refine(width=self.user_options.refine_width)

        if not self.user_options.orthogonal:
            self.addPointAtWallToContours()
            self.distributePointsNonorthogonal()

    def addPointAtWallToContours(self):
        # maximum number of times to extend the contour when it has not yet hit the wall
        max_extend = 100

        # should the contour intersect a wall at the lower end?
        lower_wall = self.connections['lower'] is None

        # should the contour intersect a wall at the upper end?
        upper_wall = self.connections['upper'] is None

        # sfunc_orthogonal functions created after contour has been extended past wall (if
        # necessary) but before adding the wall point to the contour (as adding this point
        # makes the spacing of points on the contour not-smooth) and adjusted for the
        # change in distance after redefining startInd to be at the wall
        self.sfunc_orthogonal_list = []

        # find wall intersections
        def correct_sfunc_orthogonal(contour, sfunc_orthogonal_original):
            distance_at_original_start = contour.distance[contour.startInd]

            distance_at_wall = contour.distance[lower_intersect_index]

            # correct sfunc_orthogonal for the distance between the point at the lower
            # wall and the original start-point
            return lambda i: sfunc_orthogonal_original(i) + distance_at_original_start - distance_at_wall

        for i_contour, contour in enumerate(self.contours):
            print('finding wall intersections:',
                    str(i_contour+1)+'/'+str(len(self.contours)), end = '\r')

            # point where contour intersects the lower wall
            lower_intersect = None

            # index of the segment of the contour that intersects the lower wall
            lower_intersect_index = 0

            # point where contour intersects the upper wall
            upper_intersect = None

            # index of the segment of the contour that intersects the upper wall
            upper_intersect_index = -2
            if lower_wall:
                if upper_wall:
                    starti = len(contour)//2
                else:
                    starti = len(contour) - 1

                # find whether one of the segments of the contour already intersects the wall
                for i in range(starti, 0, -1):
                    lower_intersect = self.meshParent.equilibrium.wallIntersection(contour[i],
                            contour[i-1])
                    if lower_intersect is not None:
                        lower_intersect_index = i-1
                        break

                count = 0
                while lower_intersect is None:
                    # contour has not yet intersected with wall, so make it longer and try
                    # again
                    contour.temporaryExtend(extend_lower=1)
                    lower_intersect = self.meshParent.equilibrium.wallIntersection(contour[1],
                            contour[0])
                    count += 1
                    assert count < max_extend, 'extended contour too far without finding wall'

            if upper_wall:
                if lower_wall:
                    starti = len(contour//2)
                else:
                    starti = 0

                # find whether one of the segments of the contour already intersects the wall
                for i in range(starti, len(contour) - 1):
                    upper_intersect = self.meshParent.equilibrium.wallIntersection(contour[i],
                            contour[i+1])
                    if upper_intersect is not None:
                        upper_intersect_index = i
                        break

                count = 0
                while upper_intersect is None:
                    # contour has not yet intersected with wall, so make it longer and try
                    # again
                    contour.temporaryExtend(extend_upper=1)
                    upper_intersect = self.meshParent.equilibrium.wallIntersection(contour[-2],
                            contour[-1])
                    count += 1
                    assert count < max_extend, 'extended contour too far without finding wall'

            # now add points on the wall(s) to the contour
            if lower_wall:
                # need to construct a new sfunc which gives distance from the wall, not the
                # distance from the original startInd

                # this sfunc would put the points at the positions along the contour where the
                # grid would be orthogonal
                sfunc_orthogonal_original = contour.contourSfunc()

                # now make lower_intersect_index the index where the point at the wall is
                # check whether one of the points is already on the wall
                if calc_distance(contour[lower_intersect_index], lower_intersect) < self.atol:
                    pass
                elif calc_distance(contour[lower_intersect_index+1], lower_intersect) < self.atol:
                    lower_intersect_index = lower_intersect_index + 1
                else:
                    # otherwise insert a new point
                    lower_intersect_index += 1
                    contour.insert(lower_intersect_index, lower_intersect)

                # contour.contourSfunc() would put the points at the positions along the
                # contour where the grid would be orthogonal
                # need to correct sfunc_orthogonal for the distance between the point at
                # the lower wall and the original start-point
                sfunc_orthogonal = correct_sfunc_orthogonal(contour,
                        sfunc_orthogonal_original)

                # start contour from the wall
                contour.startInd = lower_intersect_index

            if upper_wall:
                if lower_wall:
                    # need to correct for point already added at lower wall
                    upper_intersect_index += 1

                # this sfunc would put the points at the positions along the contour where the
                # grid would be orthogonal
                sfunc_orthogonal = contour.contourSfunc()

                # now make upper_intersect_index the index where the point at the wall is
                # check whether one of the points is already on the wall
                if calc_distance(contour[upper_intersect_index], upper_intersect) < self.atol:
                    pass
                elif calc_distance(contour[upper_intersect_index+1], upper_intersect) < self.atol:
                    upper_intersect_index = upper_intersect_index + 1
                else:
                    # otherwise insert a new point
                    upper_intersect_index += 1
                    contour.insert(upper_intersect_index, upper_intersect)

                # end point is now at the wall
                contour.endInd = upper_intersect_index

            self.sfunc_orthogonal_list.append(sfunc_orthogonal)

            contour.refine(width=self.user_options.refine_width)

    def distributePointsNonorthogonal(self):
        # regrid the contours (which all know where the wall is)
        for i_contour, contour in enumerate(self.contours):
            print('distributing points on contour:',
                    str(i_contour+1)+'/'+str(len(self.contours)), end = '\r')

            contour_is_separatrix = (numpy.abs((contour.psival -
                self.meshParent.equilibrium.psi_sep[0]) /
                self.meshParent.equilibrium.psi_sep[0]) < 1.e-9)

            def surface_vec(lower):
                if contour_is_separatrix:
                    if lower:
                        if self.equilibriumRegion.wallSurfaceAtStart is not None:
                            return self.equilibriumRegion.wallSurfaceAtStart
                        else:
                            # Use poloidal spacing on a separatrix contour
                            return None
                    else:
                        if self.equilibriumRegion.wallSurfaceAtEnd is not None:
                            return self.equilibriumRegion.wallSurfaceAtEnd
                        else:
                            # Use poloidal spacing on a separatrix contour
                            return None

                if i_contour == 0:
                    c_in = self.contours[0]
                else:
                    # contours are being changed, but start and end points are fixed so it is OK
                    # to use contours[i_contour-1] anyway
                    c_in = self.contours[i_contour-1]
                if i_contour == len(self.contours) - 1:
                    c_out = self.contours[i_contour]
                else:
                    c_out = self.contours[i_contour+1]
                if lower:
                    p_in = c_in[c_in.startInd]
                    p_out = c_out[c_out.startInd]
                else:
                    p_in = c_in[c_in.endInd]
                    p_out = c_out[c_out.endInd]
                return [p_out.R - p_in.R, p_out.Z - p_in.Z]

            if self.user_options.nonorthogonal_spacing_method == 'orthogonal':
                warnings.warn('\'orthogonal\' option is not currently compatible with '
                        'extending grid past targets')
                sfunc = self.sfunc_orthogonal_list[i_contour]
            elif self.user_options.nonorthogonal_spacing_method == 'fixed_poloidal':
                # this sfunc gives a fixed poloidal spacing at beginning and end of contours
                sfunc = self.equilibriumRegion.getSfuncFixedSpacing(
                        2*self.ny_noguards + 1, contour.totalDistance(), method='polynomial')
            elif self.user_options.nonorthogonal_spacing_method == 'poloidal_orthogonal_combined':
                sfunc = self.equilibriumRegion.combineSfuncs(contour,
                        self.sfunc_orthogonal_list[i_contour])
            elif self.user_options.nonorthogonal_spacing_method == 'fixed_perp_lower':
                sfunc = self.equilibriumRegion.getSfuncFixedPerpSpacing(
                        2*self.ny_noguards + 1, contour, surface_vec(True), True)
            elif self.user_options.nonorthogonal_spacing_method == 'fixed_perp_upper':
                sfunc = self.equilibriumRegion.getSfuncFixedPerpSpacing(
                        2*self.ny_noguards + 1, contour, surface_vec(False), False)
            elif self.user_options.nonorthogonal_spacing_method == 'perp_orthogonal_combined':
                sfunc = self.equilibriumRegion.combineSfuncs(contour,
                        self.sfunc_orthogonal_list[i_contour],
                        surface_vec(True), surface_vec(False))
            elif self.user_options.nonorthogonal_spacing_method == 'combined':
                if self.equilibriumRegion.wallSurfaceAtStart is not None:
                    # use poloidal spacing near a wall
                    surface_vec_lower = None
                else:
                    # use perp spacing
                    surface_vec_lower = surface_vec(True)
                if self.equilibriumRegion.wallSurfaceAtEnd is not None:
                    # use poloidal spacing near a wall
                    surface_vec_upper = None
                else:
                    # use perp spacing
                    surface_vec_upper = surface_vec(False)
                sfunc = self.equilibriumRegion.combineSfuncs(contour,
                        self.sfunc_orthogonal_list[i_contour],
                        surface_vec_lower, surface_vec_upper)
            else:
                raise ValueError('Unrecognized option \'' +
                        str(self.user_options.nonorthogonal_spacing_method)
                        + '\' for nonorthogonal poloidal spacing function')

            contour.regrid(2*self.ny_noguards + 1, sfunc=sfunc,
                    width=self.user_options.refine_width,
                    extend_lower=self.equilibriumRegion.extend_lower,
                    extend_upper=self.equilibriumRegion.extend_upper)

    def globalXInd(self, i):
        """
        Get the global x-index in the set of MeshRegions connected radially to this one of
        the point with local x-index i. Define so globalXInd=0 is at the primary separatrix
        """
        if self.radialIndex >= self.equilibriumRegion.separatrix_radial_index:
            # outside separatrix
            return i + sum(2*n for n in
                    self.equilibriumRegion.options.nx[self.equilibriumRegion.separatrix_radial_index:self.radialIndex])
        else:
            # inside separatrix
            return i - sum(2*n for n in
                    self.equilibriumRegion.options.nx[self.equilibriumRegion.separatrix_radial_index:self.radialIndex:-1])

    def fillRZ(self):
        """
        Fill the Rxy, Rxy_ylow and Zxy, Zxy_ylow arrays for this region

        xlow values include the outer point, after the final cell-centre grid point
        ylow values include the upper point, above the final cell-centre grid point
        """

        self.Rxy = MultiLocationArray(self.nx, self.ny)
        self.Zxy = MultiLocationArray(self.nx, self.ny)

        self.Rxy.centre = numpy.array([[p.R for p in contour[1::2]]
            for contour in self.contours[1::2]])

        self.Rxy.ylow = numpy.array([[p.R for p in contour[0::2]]
            for contour in self.contours[1::2]])

        self.Rxy.xlow = numpy.array([[p.R for p in contour[1::2]]
            for contour in self.contours[0::2]])

        self.Zxy.centre = numpy.array( [[p.Z for p in contour[1::2]]
            for contour in self.contours[1::2]])

        self.Zxy.ylow = numpy.array( [[p.Z for p in contour[0::2]]
            for contour in self.contours[1::2]])

        self.Zxy.xlow = numpy.array([[p.Z for p in contour[1::2]]
            for contour in self.contours[0::2]])

        self.Rxy.corners = numpy.array( [[p.R for p in contour[0::2]]
            for contour in self.contours[0::2]])
        self.Zxy.corners = numpy.array( [[p.Z for p in contour[0::2]]
            for contour in self.contours[0::2]])

        # Fix up the corner values at the X-points. Because the PsiContour have to start
        # slightly away from the X-point in order for the integrator to go in the right
        # direction, the points that should be at the X-point will be slighly displaced,
        # and will not be consistent between regions. So replace these points with the
        # X-point position instead.
        xpoint = self.equilibriumRegion.xPointsAtStart[self.radialIndex]
        if xpoint is not None:
            self.Rxy.corners[0,0] = xpoint.R
            self.Zxy.corners[0,0] = xpoint.Z

        xpoint = self.equilibriumRegion.xPointsAtStart[self.radialIndex+1]
        if xpoint is not None:
            self.Rxy.corners[-1,0] = xpoint.R
            self.Zxy.corners[-1,0] = xpoint.Z

        xpoint = self.equilibriumRegion.xPointsAtEnd[self.radialIndex]
        if xpoint is not None:
            self.Rxy.corners[0,-1] = xpoint.R
            self.Zxy.corners[0,-1] = xpoint.Z

        xpoint = self.equilibriumRegion.xPointsAtEnd[self.radialIndex+1]
        if xpoint is not None:
            self.Rxy.corners[-1,-1] = xpoint.R
            self.Zxy.corners[-1,-1] = xpoint.Z

    def getRZBoundary(self):
        # Upper value of ylow array logically overlaps with the lower value in the upper
        # neighbour. They should be close, but aren't guaranteed to be identical already
        # because they were taken from separate PsiContour obects. Use the value from the
        # upper neighbour to ensure consistency.
        # Also do similarly for the corner arrays.
        # Don't need to do this for the x-boundaries, because there the PsiContour
        # objects are shared between neighbouring regions.
        #
        # This needs to be a separate method from fillRZ() so that it can be called after
        # all regions have filled their Rxy and Zxy arrays.
        if self.connections['upper'] is not None:
            up = self.getNeighbour('upper')
            self.Rxy.ylow[:,-1] = up.Rxy.ylow[:,0]
            self.Zxy.ylow[:,-1] = up.Zxy.ylow[:,0]
            self.Rxy.corners[:,-1] = up.Rxy.corners[:,0]
            self.Zxy.corners[:,-1] = up.Zxy.corners[:,0]

    def geometry(self):
        """
        Calculate geometrical quantities for this region
        """

        self.psixy = self.meshParent.equilibrium.psi(self.Rxy, self.Zxy)

        self.dx = MultiLocationArray(self.nx, self.ny)
        self.dx.centre = (self.psi_vals[2::2] - self.psi_vals[:-2:2])[:, numpy.newaxis]
        self.dx.ylow = (self.psi_vals[2::2] - self.psi_vals[:-2:2])[:, numpy.newaxis]

        if self.psi_vals[0] > self.psi_vals[-1]:
            # x-coordinate is -psixy so x always increases radially across grid
            self.bpsign = -1.
            self.xcoord = -self.psixy
        else:
            self.bpsign = 1.
            self.xcoord = self.psixy

        self.dy = MultiLocationArray(self.nx, self.ny)
        self.dy.centre = self.meshParent.dy_scalar
        self.dy.ylow = self.meshParent.dy_scalar
        self.dy.xlow = self.meshParent.dy_scalar
        self.dy.corners = self.meshParent.dy_scalar

        self.Brxy = self.meshParent.equilibrium.Bp_R(self.Rxy, self.Zxy)
        self.Bzxy = self.meshParent.equilibrium.Bp_Z(self.Rxy, self.Zxy)
        self.Bpxy = numpy.sqrt(self.Brxy**2 + self.Bzxy**2)

        # determine direction - dot Bp with Grad(y) vector
        # evaluate in 'sol' at outer radial boundary
        Bp_dot_grady = (
            self.Brxy.centre[-1, self.ny//2]
            *(self.Rxy.centre[-1, self.ny//2 + 1] - self.Rxy.centre[-1, self.ny//2 - 1])
            + self.Bzxy.centre[-1, self.ny//2]
              *(self.Zxy.centre[-1, self.ny//2 + 1] - self.Zxy.centre[-1, self.ny//2 - 1]) )
        #print(self.myID, self.psi_vals[0], self.psi_vals[1], Bp_dot_grady)
        #print(self.Brxy.centre[-1, self.ny//2], self.Bzxy.centre[-1, self.ny//2],
        #        (self.Rxy.centre[-1, self.ny//2 - 1], self.Rxy.centre[-1, self.ny//2 +
        #            1]), (self.Zxy.centre[-1, self.ny//2 - 1], self.Zxy.centre[-1, self.ny//2 + 1]))
        if Bp_dot_grady < 0.:
            print("Poloidal field is in opposite direction to Grad(theta) -> Bp negative")
            self.Bpxy = -self.Bpxy
            if self.bpsign > 0.:
                raise ValueError("Sign of Bp should be negative? (note this check will "
                        "raise an exception when bpsign was correct if you only have a "
                        "private flux region)")
        else:
            if self.bpsign < 0.:
                raise ValueError("Sign of Bp should be negative? (note this check will "
                        "raise an exception when bpsign was correct if you only have a "
                        "private flux region)")

        # Get toroidal field from poloidal current function fpol
        self.Btxy = self.meshParent.equilibrium.fpol(self.psixy) / self.Rxy

        self.Bxy = numpy.sqrt(self.Bpxy**2 + self.Btxy**2)

        self.hy = self.calcHy()

        #if not self.user_options.orthogonal:
        #    # Calculate beta (angle between x and y coordinates), used for non-orthogonal grid
        #    # Also calculate radial grid spacing
        #    self.beta, self.hrad = self.calcBeta()

        #    # eta is the polodial non-orthogonality parameter
        #    self.eta = numpy.sin(self.beta)
        #else:
        #    self.beta.centre = 0.
        #    self.eta.centre = 0.

        # variation of toroidal angle with y following a field line. Called 'pitch' in
        # Hypnotoad1 because if y was the poloidal angle then dphidy would be the pitch
        # angle.
        self.dphidy = self.hy * self.Btxy / (self.Bpxy * self.Rxy)

    def calcMetric(self):
        """
        Calculate the metrics using geometrical information calculated in geometry().
        Needs to be a separate method as zShift can only be calculated when calcZShift()
        has been called on the MeshRegion at the beginning of the y-group. To ensure this,
        call geometry() on all regions first, then calcMetric on all regions.
        """
        if not self.user_options.shiftedmetric:
            # To implement the shiftedmetric==False case, would have to define a
            # consistent zShift=0 location for all regions, for example in the style of
            # Hypnotoad1. This could be done by a particular implementation of 'Mesh'
            # (e.g. 'BoutMesh') before calling this method. Needs to be a particular
            # implementation which knows about the topology of the grid - still not clear
            # it is possible to do consistently, e.g. in private-flux regions.
            raise ValueError("'shiftedmetric == False' not handled at present.\n"
                             "Cannot make grid for field-aligned toroidal coordinates "
                             "without making zShift consistent between all regions. "
                             "Don't know how to do this in general, and haven't "
                             "implemented the Hypnototoad1-style solution as it does not "
                             "seem consistent in the private-flux region, or the "
                             "inner-SOL of a double-null configuration.")
            # integrated shear
            self.sinty = self.DDX('zShift')
            self.I = self.sinty
        else:
            # Zero integrated shear, because the coordinate system is defined locally to
            # each value of y, and defined to have no shear.
            # In this case zShift only needs to be defined consistently *along* each field
            # line - don't need to be able to take radial (x-direction) derivatives. This
            # means different (radial) regions can use different locations for where
            # zShift=0.
            self.I = MultiLocationArray(self.nx, self.ny).zero()

        # Here ShiftTorsion = d2phidxdy
        # Haven't checked this is exactly the quantity needed by BOUT++...
        # ShiftTorsion is only used in Curl operator - Curl is rarely used.
        self.ShiftTorsion = self.DDX('#dphidy')

        self.g11 = (self.Rxy*self.Bpxy)**2
        self.g22 = 1./self.hy**2
        self.g33 = self.I*self.g11 + (self.dphidy/self.hy)**2 + 1./self.Rxy**2
        self.g12 = MultiLocationArray(self.nx, self.ny).zero()
        self.g13 = -self.I*self.g11
        self.g23 = -self.dphidy/self.hy**2

        self.J = self.hy / self.Bpxy

        self.g_11 = 1./self.g11 + (self.I*self.Rxy)**2
        self.g_22 = self.hy**2 + (self.Rxy*self.dphidy)**2
        self.g_33 = self.Rxy**2
        self.g_12 = self.Rxy**2*self.dphidy*self.I
        self.g_13 = self.Rxy**2*self.I
        self.g_23 = self.dphidy*self.Rxy**2

        # check Jacobian is OK
        Jcheck = self.bpsign*1./numpy.sqrt(self.g11*self.g22*self.g33
                + 2.*self.g12*self.g13*self.g23 - self.g11*self.g23**2
                - self.g22*self.g13**2 - self.g33*self.g12**2)
        # ignore grid points at X-points as J should diverge there (as Bp->0)
        if self.equilibriumRegion.xPointsAtStart[self.radialIndex] is not None:
            Jcheck.corners[0, 0] = self.J.corners[0,0]
        if self.equilibriumRegion.xPointsAtStart[self.radialIndex + 1] is not None:
            Jcheck.corners[-1, 0] = self.J.corners[-1,0]
        if self.equilibriumRegion.xPointsAtEnd[self.radialIndex] is not None:
            Jcheck.corners[0, -1] = self.J.corners[0, -1]
        if self.equilibriumRegion.xPointsAtEnd[self.radialIndex + 1] is not None:
            Jcheck.corners[-1, -1] = self.J.corners[-1, -1]

        check = numpy.abs(self.J - Jcheck) / numpy.abs(self.J) < self.user_options.geometry_rtol
        def ploterror(location):
            if location == 'centre':
                thisJ = self.J.centre
                this_one_over_sqrt_g = Jcheck.centre
            elif location == 'ylow':
                thisJ = self.J.ylow
                this_one_over_sqrt_g = Jcheck.ylow
            elif location == 'xlow':
                thisJ = self.J.xlow
                this_one_over_sqrt_g = Jcheck.xlow
            elif location == 'corners':
                thisJ = self.J.corners
                this_one_over_sqrt_g = Jcheck.corners
            else:
                raise ValueError('wrong location argument: '+str(location))
            print(self.name, 'rtol = ' + str(self.user_options.geometry_rtol))
            from matplotlib import pyplot
            pyplot.figure(location)
            pyplot.subplot(221)
            pyplot.pcolor(thisJ)
            pyplot.title('J')
            pyplot.colorbar()
            pyplot.subplot(222)
            pyplot.pcolor(this_one_over_sqrt_g)
            pyplot.title('1/sqrt(g)')
            pyplot.colorbar()
            pyplot.subplot(223)
            pyplot.pcolor(thisJ - this_one_over_sqrt_g)
            pyplot.title('abs difference')
            pyplot.colorbar()
            pyplot.subplot(224)
            pyplot.pcolor((thisJ - this_one_over_sqrt_g)/thisJ)
            pyplot.title('rel difference')
            pyplot.colorbar()
            pyplot.show()
        if not numpy.all(check.centre):
            ploterror('centre')
        if not numpy.all(check.ylow):
            ploterror('ylow')
        if not numpy.all(check.xlow):
            ploterror('xlow')
        if not numpy.all(check.corners):
            ploterror('corners')
        assert numpy.all(check.centre), 'Jacobian should be consistent with 1/sqrt(det(g)) calculated from the metric tensor'
        assert numpy.all(check.ylow), 'Jacobian should be consistent with 1/sqrt(det(g)) calculated from the metric tensor'
        assert numpy.all(check.xlow), 'Jacobian should be consistent with 1/sqrt(det(g)) calculated from the metric tensor'
        assert numpy.all(check.corners), 'Jacobian should be consistent with 1/sqrt(det(g)) calculated from the metric tensor'

        # curvature terms
        self.calc_curvature()

    def calc_curvature(self):
        if False:
            # calculate curl on x-y grid
            self.curl_bOverB_x = ( -2.*self.bpsign*self.Bpxy*self.Btxy*self.Rxy
                                    / (self.hy*self.Bxy**3) * self.DDY('#Bxy') )
            self.curl_bOverB_y = ( -self.bpsign*self.Bpxy/self.hy
                                    * self.DDX('#Btxy*#Rxy/#Bxy**2') )
            self.curl_bOverB_z = ( self.Bpxy**3/(self.hy*self.Bxy**2)
                                     * self.DDX('#hy/#Bpxy')
                                   - self.Btxy*self.Rxy/self.Bxy**2
                                     * self.DDX('#Btxy/#Rxy')
                                   - self.I*self.curl_bOverB_x)
        else:
            # Calculate Curl(b/B) in R-Z, then project onto x-y-z components
            equilib = self.meshParent.equilibrium
            psi = equilib.psi
            fpol = lambda R,Z: equilib.fpol(psi(R,Z))
            fpolprime = lambda R,Z: equilib.fpolprime(psi(R,Z))
            BR = equilib.Bp_R
            BZ = equilib.Bp_Z
            d2psidR2 = equilib.d2psidR2
            d2psidZ2 = equilib.d2psidZ2
            d2psidRdZ = equilib.d2psidRdZ

            # Toroidal component of B
            Bphi = lambda R,Z: fpol(R,Z) / R

            # B^2
            B2 = lambda R,Z: ( BR(R,Z)**2 + BZ(R,Z)**2 + Bphi(R,Z)**2 )

            # d(B^2)/dR
            dB2dR = lambda R,Z: ( -2./R * B2(R,Z)
                    + 2./R * (-BZ(R,Z)*d2psidR2(R,Z) + BR(R,Z)*d2psidRdZ(R,Z)
                              - fpol(R,Z)*fpolprime(R,Z)*BZ(R,Z)) )

            # d(B^2)/dZ
            dB2dZ = lambda R,Z: 2./R * (-BZ(R,Z)*d2psidRdZ(R,Z) + BR(R,Z)*d2psidZ2(R,Z)
                                        + fpol(R,Z)*fpolprime(R,Z)*BR(R,Z))

            # dBphi/dR
            dBphidR = lambda R,Z: -fpolprime(R,Z)*BZ(R,Z) - fpol(R,Z)/R**2

            # dBphi/dZ
            dBphidZ = lambda R,Z: fpolprime(R,Z)*BR(R,Z)

            # dBZ/dR
            dBZdR = lambda R,Z: -d2psidR2(R,Z)/R - BZ(R,Z)/R

            # dBR/dZ
            dBRdZ = lambda R,Z: d2psidZ2(R,Z)/R

            # curl(b/B)
            curl_bOverB_R = lambda R,Z: dBphidZ(R,Z)/B2(R,Z) - Bphi(R,Z)/B2(R,Z)**2 * dB2dZ(R,Z)
            curl_bOverB_Z = lambda R,Z: -dBphidR(R,Z)/B2(R,Z) + Bphi(R,Z)/B2(R,Z)**2 * dB2dR(R,Z)
            curl_bOverB_phi = lambda R,Z: ( dBZdR(R,Z)/B2(R,Z) - BZ(R,Z)/B2(R,Z)**2 * dB2dR(R,Z)
                                            - dBRdZ(R,Z)/B2(R,Z) + BR(R,Z)/B2(R,Z)**2 * dB2dZ(R,Z) )

            curl_bOverB_R = curl_bOverB_R(self.Rxy, self.Zxy)
            curl_bOverB_Z = curl_bOverB_Z(self.Rxy, self.Zxy)
            curl_bOverB_phi = curl_bOverB_phi(self.Rxy, self.Zxy)

        if self.user_options.curvature_type == 'curl(b/B)':
            self.bxcvx = self.Bxy/2. * self.curl_bOverB_x
            self.bxcvy = self.Bxy/2. * self.curl_bOverB_y
            self.bxcvz = self.Bxy/2. * self.curl_bOverB_z
        elif self.user_options.curvature_type == 'bxkappa':
            self.bxcvx = float('nan')
            self.bxcvy = float('nan')
            self.bxcvz = float('nan')
        else:
            raise ValueError('Unrecognized option \''
                    + str(self.user_options.curvature_type) + '\' for curvature type')

    def calcHy(self):
        # hy = |Grad(theta)|
        # hy = dtheta/ds at constant psi, phi when psi and theta are orthogonal
        # approx dtheta/sqrt((R(j+1/2)-R(j-1/2))**2 + (Z(j+1/2)-Z(j-1/2)**2)
        if not self.user_options.orthogonal:
            warnings.warn('need to check that this is correct for non-orthogonal grids')

        hy = MultiLocationArray(self.nx, self.ny)
        # contours have accurately calculated distances
        # calculate distances between j+/-0.5
        for i in range(self.nx):
            d = numpy.array(self.contours[2*i + 1].distance)
            hy.centre[i, :] = (d[2::2] - d[:-2:2])
            hy.ylow[i, 1:-1] = (d[3:-1:2] - d[1:-3:2])
            if self.connections['lower'] is not None:
                cbelow = self.getNeighbour('lower').contours[2*i + 1]
                hy.ylow[i, 0] = (d[1] - d[0] + cbelow.distance[-1] - cbelow.distance[-2])
            else:
                # no region below, so estimate distance to point before '0' as the same as
                # from '0' to '1'
                hy.ylow[i, 0] = 2.*(d[1] - d[0])
            if self.connections['upper'] is not None:
                cabove = self.getNeighbour('upper').contours[2*i + 1]
                hy.ylow[i, -1] = (d[-1] - d[-2] + cabove.distance[1] - cabove.distance[0])
            else:
                # no region below, so estimate distance to point before '0' as the same as
                # from '0' to '1'
                hy.ylow[i, -1] = 2.*(d[-1] - d[-2])

        for i in range(self.nx + 1):
            d = numpy.array(self.contours[2*i].distance)
            hy.xlow[i, :] = (d[2::2] - d[:-2:2])
            hy.corners[i, 1:-1] = (d[3:-1:2] - d[1:-3:2])
            if self.connections['lower'] is not None:
                cbelow = self.getNeighbour('lower').contours[2*i]
                hy.corners[i, 0] = (d[1] - d[0] + cbelow.distance[-1] - cbelow.distance[-2])
            else:
                # no region below, so estimate distance to point before '0' as the same as
                # from '0' to '1'
                hy.corners[i, 0] = 2.*(d[1] - d[0])
            if self.connections['upper'] is not None:
                cabove = self.getNeighbour('upper').contours[2*i]
                hy.corners[i, -1] = (d[-1] - d[-2] + cabove.distance[1] - cabove.distance[0])
            else:
                # no region below, so estimate distance to point before '0' as the same as
                # from '0' to '1'
                hy.corners[i, -1] = 2.*(d[-1] - d[-2])

        hy /= self.dy

        assert numpy.all(hy.centre > 0.), 'hy.centre should always be positive'
        assert numpy.all(hy.xlow > 0.), 'hy.xlow should always be positive'
        assert numpy.all(hy.ylow > 0.), 'hy.ylow should always be positive'
        assert numpy.all(hy.corners > 0.), 'hy.corners should always be positive'

        return hy

    def calcBeta(self, ylow=False):
        """
        beta is the angle between x and y coordinates, used for non-orthogonal grid.
        Also calculate radial grid spacing, hrad
        """
        #raise ValueError("non-orthogonal grids not calculated yet")
        warnings.warn("non-orthogonal grids not calculated yet")

        #if not ylow:
        #    # need to multiply f_R and f_Z by bpsign because we want the radially-outward
        #    # vector perpendicular to psi contours, and if bpsign is negative then psi
        #    # increases inward instead of outward so (f_R,f_Z) would be in the opposite
        #    # direction
        #    # Actually want the angle of the vector in the y-direction, i.e. (f_Z,-f_R)
        #    angle_grad_psi = numpy.arctan2(
        #            self.bpsign*self.meshParent.equilibrium.f_Z(self.Rxy, self.Zxy),
        #            -self.bpsign*self.meshParent.equilibrium.f_R(self.Rxy, self.Zxy))

        #    R = numpy.zeros([self.nx + 1, self.ny])
        #    R[:-1, :] = self.Rxy_xlow
        #    R[-1, :] = self.Rxy_extra_outer
        #    Z = numpy.zeros([self.nx + 1, self.ny])
        #    Z[:-1 :] = self.Zxy_xlow
        #    Z[-1, :] = self.Zxy_extra_outer
        #    # could calculate radial grid spacing - is it ever needed?
        #    hrad = numpy.sqrt((R[1:,:] - R[:-1,:])**2 + (Z[1:,:] - Z[:-1,:])**2)

        #    dR = R[1:,:] - R[:-1,:]
        #    dZ = Z[1:,:] - Z[:-1,:]
        #    angle_dr = numpy.arctan2(dR, dZ)
        #else:
        #    # need to multiply f_R and f_Z by bpsign because we want the radially-outward
        #    # vector perpendicular to psi contours, and if bpsign is negative then psi
        #    # increases inward instead of outward so (f_R,f_Z) would be in the opposite
        #    # direction
        #    # Actually want the angle of the vector in the y-direction, i.e. (f_Z,-f_R)
        #    angle_grad_psi = numpy.arctan2(
        #            self.bpsign*self.meshParent.equilibrium.f_Z(self.Rxy_ylow, self.Zxy_ylow),
        #            -self.bpsign*self.meshParent.equilibrium.f_R(self.Rxy_ylow, self.Zxy_ylow))

        #    # could calculate radial grid spacing - is it ever needed?
        #    ## for hrad at ylow, can use Rcorners and Zcorners
        #    hrad = numpy.sqrt((self.Rcorners[1:,:-1] - self.Rcorners[:-1,:-1])**2 +
        #                      (self.Zcorners[1:,:-1] - self.Zcorners[:-1,:-1])**2)

        #    dR = self.Rcorners[1:,:-1] - self.Rcorners[:-1,:-1]
        #    dZ = self.Zcorners[1:,:-1] - self.Zcorners[:-1,:-1]
        #    angle_dr = numpy.arctan2(dR, dZ)

        #return (angle_grad_psi - angle_dr - numpy.pi/2.), hrad

    def calcZShift(self):
        """
        Calculate zShift by integrating dphidy in y.
        """
        # Integrate using all available points - centre+ylow or xlow+corner.
        # Integrate from lower boundary on open field lines.
        # Integrate from lower side of MeshRegion with yGroupIndex=0 on closed field
        # lines.
        # Use trapezoid rule. If int_f = \int f dy
        # int_f.centre[j] = int_f.centre[j-1]
        #                   + 0.5*(f.centre[j-1] + f.ylow[j]) * (0.5*dy.centre[j-1])
        #                   + 0.5*(f.ylow[j] + f.centre[j]) * (0.5*dy.centre[j])
        #                 = i_centre[j-1] + i_ylow_upper[j]
        #                   + i_ylow_lower[j] + i_centre[j]
        # At the moment dy is a constant, but we allow for future changes with variable
        # grid-spacing in y. The cell-centre points should be half way between the
        # cell-face points, so the distance between centre[j-1] and ylow[j] is
        # 0.5*dy[j-1], and the distace between ylow[j] and centre[j] is 0.5*dy[j]
        #
        # Also
        # int_f.ylow[j] = int_f.ylow[j-1]
        #                 + 0.5*(f.ylow[j-1] + f.centre[j-1]) * (0.5*dy.centre[j-1])
        #                 + 0.5*(f.centre[j-1] + f.ylow[j]) * (0.5*dy.centre[j-1])
        #               = i_ylow_lower[j-1] + i_centre[j-1]
        #                 + i_centre[j-1] + i_ylow_upper[j]

        # Cannot just test 'connections['lower'] is not None' because periodic regions
        # always have a lower connection - requires us to give a yGroupIndex to each
        # region when creating the groups.
        if self.yGroupIndex is not 0:
            return None

        region = self
        region.zShift = MultiLocationArray(region.nx, region.ny)
        while True:
            # calculate integral for field lines with centre and ylow points
            i_centre = 0.25*numpy.cumsum(region.dphidy.centre * region.dy.centre, axis=1)
            i_ylow_lower = 0.25*numpy.cumsum(region.dphidy.ylow[:, :-1] \
                           * region.dy.centre, axis=1)
            i_ylow_upper = 0.25*numpy.cumsum(region.dphidy.ylow[:, 1:] \
                           * region.dy.centre, axis=1)

            region.zShift.centre[:,0] = region.zShift.ylow[:, 0] \
                                        + i_ylow_lower[:, 0] + i_centre[:, 0]
            region.zShift.centre[:,1:] = region.zShift.ylow[:, 0, numpy.newaxis] \
                                         + i_centre[:, :-1] + i_ylow_upper[:, :-1] \
                                         + i_ylow_lower[:, 1:] + i_centre[:, 1:]

            region.zShift.ylow[:, 1:] = region.zShift.ylow[:, 0, numpy.newaxis] \
                                        + i_ylow_lower + 2.*i_centre \
                                        + i_ylow_upper

            # repeat for field lines with xlow and corner points
            i_xlow = 0.25*numpy.cumsum(region.dphidy.xlow * region.dy.xlow, axis=1)
            i_corners_lower = 0.25*numpy.cumsum(region.dphidy.corners[:, :-1] \
                              * region.dy.xlow, axis=1)
            i_corners_upper = 0.25*numpy.cumsum(region.dphidy.corners[:, 1:] \
                              * region.dy.xlow, axis=1)

            region.zShift.xlow[:,0] = region.zShift.corners[:, 0] \
                                        + i_corners_lower[:, 0] + i_xlow[:, 0]
            region.zShift.xlow[:,1:] = region.zShift.corners[:, 0, numpy.newaxis] \
                                         + i_xlow[:, :-1] + i_corners_upper[:, :-1] \
                                         + i_corners_lower[:, 1:] + i_xlow[:, 1:]

            region.zShift.corners[:, 1:] = region.zShift.corners[:, 0, numpy.newaxis] \
                                        + i_corners_lower + 2.*i_xlow \
                                        + i_corners_upper

            next_region = region.getNeighbour('upper')
            if next_region is None:
                break
            else:
                next_region.zShift = MultiLocationArray(next_region.nx, next_region.ny)
                next_region.zShift.ylow[:, 0] = region.zShift.ylow[:, -1]
                next_region.zShift.corners[:, 0] = region.zShift.corners[:, -1]
                region = next_region

    def getNeighbour(self, face):
        if self.connections[face] is None:
            return None
        else:
            return self.meshParent.regions[self.connections[face]]

    def _eval_from_region(self, expr, region=None, component=None):
        # Utility routine to evaluate an expression using different MeshRegions
        # Names of fields belonging to the MeshRegion are indicated by a '#' in expr, e.g.
        # if 'foo' and 'bar' are two member variables, we could have expr='#foo + #bar'

        if region is None:
            region_string = 'self'
        else:
            region_string = 'self.getNeighbour(\''+region+'\')'

        if component is None:
            component = ''
        else:
            component = '.' + component

        # replace the name of the field with an expression to get that field from the
        # MeshRegion 'region'
        expr = re.sub('#(\\w+)', region_string + '.__dict__[\'\\1\']' + component, expr)

        return eval(expr)

    def DDX(self, expr):
        # x-derivative of a MultiLocationArray, calculated with 2nd order central
        # differences

        f = self._eval_from_region(expr)

        result = MultiLocationArray(self.nx, self.ny)

        if f.xlow is not None:
            result.centre[...] = (f.xlow[1:, :] - f.xlow[:-1, :]) / self.dx.centre
        else:
            warnings.warn('No xlow field available to calculate DDX(' + name + ').centre')
        if f.corners is not None:
            result.ylow[...] = (f.corners[1:, :] - f.corners[:-1, :]) / self.dx.ylow
        else:
            warnings.warn('No corners field available to calculate DDX(' + name + ').ylow')

        if f.centre is not None:
            result.xlow[1:-1, :] = (f.centre[1:, :] - f.centre[:-1, :]) / self.dx.xlow[1:-1, :]
            if self.connections['inner'] is not None:
                f_inner = self._eval_from_region(expr, 'inner', 'centre[-1, :]')
                result.xlow[0, :] = (f.centre[0, :] - f_inner) / self.dx.xlow[0, :]
            else:
                result.xlow[0, :] = (f.centre[0, :] - f.xlow[0, :]) / (self.dx.xlow[0, :]/2.)
            if self.connections['outer'] is not None:
                f_outer = self._eval_from_region(expr, 'outer', 'centre[0, :]')
                result.xlow[-1, :] = (f_outer - f.centre[-1, :]) / self.dx.xlow[-1, :]
            else:
                result.xlow[-1, :] = (f.xlow[-1, :] - f.centre[-1, :]) / (self.dx.xlow[-1, :]/2.)
        else:
            warnings.warn('No centre field available to calculate DDX(' + name + ').xlow')

        if f.ylow is not None:
            result.corners[1:-1, :] = (f.ylow[1:, :] - f.ylow[:-1, :]) / self.dx.corners[1:-1, :]
            if self.connections['inner'] is not None:
                f_inner = self._eval_from_region(expr, 'inner', 'ylow[-1, :]')
                result.corners[0, :] = (f.ylow[0, :] - f_inner) / self.dx.corners[0, :]
            else:
                result.corners[0, :] = (f.ylow[0, :] - f.corners[0, :]) / (self.dx.corners[0, :]/2.)
            if self.connections['outer'] is not None:
                f_outer = self._eval_from_region(expr, 'outer', 'ylow[0, :]')
                result.corners[-1, :] = (f_outer - f.ylow[-1, :]) / self.dx.corners[-1, :]
            else:
                result.corners[-1, :] = (f.corners[-1, :] - f.ylow[-1, :]) / (self.dx.corners[-1, :]/2.)
        else:
            warnings.warn('No ylow field available to calculate DDX(' + name + ').corners')

        return result

    def DDY(self, expr):
        # y-derivative of a MultiLocationArray, calculated with 2nd order central
        # differences
        f = self._eval_from_region(expr)

        result = MultiLocationArray(self.nx, self.ny)

        if f.ylow is not None:
            result.centre[...] = (f.ylow[:, 1:] - f.ylow[:, :-1]) / self.dy.centre
        else:
            warnings.warn('No ylow field available to calculate DDY(' + name + ').centre')
        if f.corners is not None:
            result.xlow[...] = (f.corners[:, 1:] - f.corners[:, :-1]) / self.dy.xlow
        else:
            warnings.warn('No corners field available to calculate DDY(' + name + ').xlow')

        if f.centre is not None:
            result.ylow[:, 1:-1] = (f.centre[:, 1:] - f.centre[:, :-1]) / self.dy.ylow[:, 1:-1]
            if self.connections['lower'] is not None:
                f_lower = self._eval_from_region(expr, 'lower', 'centre[:, -1]')
                result.ylow[:, 0] = (f.centre[:, 0] - f_lower) / self.dy.ylow[:, 0]
            else:
                result.ylow[:, 0] = (f.centre[:, 0] - f.ylow[:, 0]) / (self.dy.ylow[:, 0]/2.)
            if self.connections['upper'] is not None:
                f_upper = self._eval_from_region(expr, 'upper', 'centre[:, 0]')
                result.ylow[:, -1] = (f_upper - f.centre[:, -1]) / self.dy.ylow[:, -1]
            else:
                result.ylow[:, -1] = (f.ylow[:, -1] - f.centre[:, -1]) / (self.dy.ylow[:, -1]/2.)
        else:
            warnings.warn('No centre field available to calculate DDY(' + name + ').ylow')

        if f.xlow is not None:
            result.corners[:, 1:-1] = (f.xlow[:, 1:] - f.xlow[:, :-1]) / self.dy.corners[:, 1:-1]
            if self.connections['lower'] is not None:
                f_lower = self._eval_from_region(expr, 'lower', 'xlow[:, -1]')
                result.corners[:, 0] = (f.xlow[:, 0] - f_lower) / self.dy.corners[:, 0]
            else:
                result.corners[:, 0] = (f.xlow[:, 0] - f.corners[:, 0]) / (self.dy.corners[:, 0]/2.)
            if self.connections['upper'] is not None:
                f_upper = self._eval_from_region(expr, 'upper', 'xlow[:, 0]')
                result.corners[:, -1] = (f_upper - f.xlow[:, -1]) / self.dy.corners[:, -1]
            else:
                result.corners[:, -1] = (f.corners[:, -1] - f.xlow[:, -1]) / (self.dy.corners[:, -1]/2.)
        else:
            warnings.warn('No xlow field available to calculate DDY(' + name + ').corners')

        return result

class Mesh:
    """
    Mesh represented by a collection of connected MeshRegion objects
    """
    def __init__(self, equilibrium):
        self.user_options = equilibrium.user_options
        self.options = equilibrium.options

        self.equilibrium = equilibrium

        # Get current git-commit hash of Hypnotoad2 for version-tracking
        from boututils.run_wrapper import shell_safe
        from pathlib import Path
        hypnotoad_path = str(Path(__file__).parent)
        retval, self.git_hash = shell_safe('cd ' + hypnotoad_path +
                '&& git describe --always --abbrev=0 --dirty --match "NOT A TAG"',
                pipe=True)
        self.git_hash = self.git_hash.strip()
        retval, self.git_diff = shell_safe('cd ' + hypnotoad_path +
                '&& git diff',
                pipe=True)
        self.git_diff = self.git_diff.strip()

        # Generate MeshRegion object for each section of the mesh
        self.regions = {}

        # Make consecutive numbering scheme for regions
        regionlist = []
        self.region_lookup = {}
        for reg_name,eq_reg in equilibrium.regions.items():
            for i in range(eq_reg.nSegments):
                region_number = len(regionlist)
                regionlist.append((reg_name, i))
                self.region_lookup[(reg_name, i)] = region_number

        # Get connections between regions
        self.connections = {}
        for region_id,(eq_reg,i) in enumerate(regionlist):
            self.connections[region_id] = {}
            region = equilibrium.regions[eq_reg]
            c = region.connections[i]
            for key, val in c.items():
                if val is not None:
                    self.connections[region_id][key] = self.region_lookup[val]
                else:
                    self.connections[region_id][key] = None

        self.makeRegions()

    def makeRegions(self):
        for eq_region in self.equilibrium.regions.values():
            for i in range(eq_region.nSegments):
                region_id = self.region_lookup[(eq_region.name,i)]
                eq_region_with_boundaries = eq_region.getRegridded(radialIndex=i,
                        width=self.user_options.refine_width)
                self.regions[region_id] = MeshRegion(self, region_id,
                        eq_region_with_boundaries, self.connections[region_id], i)

        # create groups that connect in x
        self.x_groups = []
        region_set = set(self.regions.values())
        while region_set:
            for region in region_set:
                if region.connections['inner'] is None:
                    break
            group = []
            while True:
                group.append(region)
                region_set.remove(region)
                region = region.getNeighbour('outer')
                if region is None or group.count(region) > 0:
                    # reached boundary or have all regions in a periodic group
                    break
            self.x_groups.append(group)

        # create groups that connect in y
        self.y_groups = []
        region_set = set(self.regions.values())
        while region_set:
            for region in region_set:
                if region.connections['lower'] is None:
                    break
                # note, if no region with connections['lower']=None is found, then some
                # arbitrary region will be 'region' after this loop. This is OK, as this
                # region must be part of a periodic group, which we will handle.
            group = []
            while True:
                assert region.yGroupIndex == None, 'region should not have been added to any yGroup before'
                region.yGroupIndex = len(group)
                group.append(region)
                region_set.remove(region)
                region = region.getNeighbour('upper')
                if region is None or group.count(region) > 0:
                    # reached boundary or have all regions in a periodic group
                    break
            self.y_groups.append(group)

    def redistributePoints(self, **kwargs):
        warnings.warn('It is not recommended to use Mesh.redistributePoints() for '
                '\'production\' output. Suggest saving the final settings to a .yaml '
                'file and creating the \'production\' grid non-interactively to ensure '
                'reproducibility.')

        self.user_options.set(**kwargs)

        assert not self.user_options.orthogonal, 'redistributePoints would do nothing for an orthogonal grid.'
        for region in self.regions.values():
            print('redistributing', region.name)
            region.equilibriumRegion.setupOptions(force=True)
            region.distributePointsNonorthogonal()

    def geometry(self):
        """
        Calculate geometrical quantities for BOUT++
        """
        print('Get RZ values')
        for region in self.regions.values():
            region.fillRZ()
        for region in self.regions.values():
            region.getRZBoundary()
        print('Calculate geometry')
        for region in self.regions.values():
            print(region.name, end = '\r')
            region.geometry()
        print('Calculate zShift')
        for region in self.regions.values():
            print(region.name, end = '\r')
            region.calcZShift()
        print('Calculate Metric')
        for region in self.regions.values():
            print(region.name, end = '\r')
            region.calcMetric()

    def plotPoints(self, xlow=False, ylow=False, corners=False):
        from matplotlib import pyplot
        from cycler import cycle

        colors = cycle(pyplot.rcParams['axes.prop_cycle'].by_key()['color'])
        for region in self.regions.values():
            c = next(colors)
            pyplot.scatter(region.Rxy.centre, region.Zxy.centre, marker='x', c=c,
                    label=region.myID)
            if xlow:
                pyplot.scatter(region.Rxy.xlow, region.Zxy.xlow, marker='1', c=c)
            if ylow:
                pyplot.scatter(region.Rxy.ylow, region.Zxy.ylow, marker='2', c=c)
            if corners:
                pyplot.scatter(region.Rxy.corners, region.Zxy.corners, marker='+', c=c)
        pyplot.legend()

    def plotPotential(self, *args, **kwargs):
        """
        Plot the flux function psi. Passes through to self.equilibrium.plotPotential.
        """
        return self.equilibrium.plotPotential(*args, **kwargs)

def followPerpendicular(f_R, f_Z, p0, A0, Avals, rtol=2.e-8, atol=1.e-8):
    """
    Follow a line perpendicular to Bp from point p0 until magnetic potential A_target is
    reached.
    """
    f = lambda A,x: (f_R(x[0], x[1]), f_Z(x[0], x[1]))
    Arange = (A0, Avals[-1])
    solution = solve_ivp(f, Arange, tuple(p0), t_eval=Avals, rtol=rtol, atol=atol,
            vectorized=True)

    return [Point2D(*p) for p in solution.y.T]

class BoutMesh(Mesh):
    """
    Mesh quantities to be written to a grid file for BOUT++

    Requires that the MeshRegion members fit together into a global logically-rectangular
    Mesh, with the topology assumed by BOUT++ (allowing complexity up to
    disconnected-double-null).

    For compatibility with BOUT++, the regions in the OrderedDict equilibrium.regions must
    be in the order: inner_lower_divertor, inner_core, inner_upper_divertor,
    outer_upper_divertor, outer_core, outer_lower_divertor. This ensures the correct
    positioning in the global logically rectangular grid. Regions are allowed to not be
    present (if they would have size 0).
    """
    def __init__(self, equilibrium, *args, **kwargs):

        super().__init__(equilibrium, *args, **kwargs)

        # nx, ny both include boundary guard cells
        eq_region0 = next(iter(self.equilibrium.regions.values()))
        self.nx = sum(eq_region0.options.nx)

        self.ny = sum(r.ny(0) for r in self.equilibrium.regions.values())

        self.ny_noguards = sum(r.ny_noguards for r in self.equilibrium.regions.values())

        self.fields_to_output = []

        # Keep ranges of global indices for each region, separately from the MeshRegions,
        # because we don't want MeshRegion objects to depend on global indices
        assert all([r.options.nx == eq_region0.options.nx for r in self.equilibrium.regions.values()]), 'all regions should have same set of x-grid sizes to be compatible with a global, logically-rectangular grid'
        x_sizes = [0] + list(eq_region0.options.nx)
        self.x_startinds = numpy.cumsum(x_sizes)
        x_regions = tuple(slice(self.x_startinds[i], self.x_startinds[i+1], None)
                     for i in range(len(self.x_startinds)-1))
        y_total = 0
        y_regions = {}
        self.y_regions_noguards = []
        for regname, region in self.equilibrium.regions.items():
            # all segments must have the same ny, i.e. same number of y-boundary guard
            # cells
            this_ny = region.ny(0)
            assert all(region.ny(i) == this_ny for i in range(region.nSegments)), 'all radial segments in an equilibrium-region must have the same ny (i.e. same number of boundary guard cells) to be compatible with a global, logically-rectangular grid'

            y_total_new = y_total + this_ny
            self.y_regions_noguards.append(region.ny_noguards)
            reg_slice = slice(y_total, y_total_new, None)
            y_total = y_total_new
            y_regions[regname] = reg_slice

        self.region_indices = {}
        for reg_name in self.equilibrium.regions:
            for i in range(len(x_regions)):
                self.region_indices[self.region_lookup[(reg_name, i)]] = numpy.index_exp[
                        x_regions[i], y_regions[reg_name]]

        # constant spacing in y for now
        self.dy_scalar = 2.*numpy.pi / self.ny_noguards

    def geometry(self):
        # Call geometry() method of base class
        super().geometry()

        def addFromRegions(name):
            self.fields_to_output.append(name)
            f = MultiLocationArray(self.nx, self.ny)
            self.__dict__[name] = f
            f.attributes = next(iter(self.regions.values())).__dict__[name].attributes
            for region in self.regions.values():
                f_region = region.__dict__[name]

                assert f.attributes == f_region.attributes, 'attributes of a field must be set consistently in every region'
                if f_region._centre_array is not None:
                    f.centre[self.region_indices[region.myID]] = f_region.centre
                if f_region._xlow_array is not None:
                    f.xlow[self.region_indices[region.myID]] = f_region.xlow[:-1,:]
                if f_region._ylow_array is not None:
                    f.ylow[self.region_indices[region.myID]] = f_region.ylow[:,:-1]
                if f_region._corners_array is not None:
                    f.corners[self.region_indices[region.myID]] = f_region.corners[:-1,:-1]

        addFromRegions('Rxy')
        addFromRegions('Zxy')
        addFromRegions('psixy')
        addFromRegions('dx')
        addFromRegions('dy')
        addFromRegions('Brxy')
        addFromRegions('Bzxy')
        addFromRegions('Bpxy')
        addFromRegions('Btxy')
        addFromRegions('Bxy')
        addFromRegions('hy')
        #if not self.user_options.orthogonal:
        #    addFromRegions('beta')
        #    addFromRegions('eta')
        addFromRegions('dphidy')
        addFromRegions('ShiftTorsion')
        addFromRegions('zShift')
        # I think IntShiftTorsion should be the same as sinty in Hypnotoad1.
        # IntShiftTorsion should never be used. It is only for some 'BOUT-06 style
        # differencing'. IntShiftTorsion is not written by Hypnotoad1, so don't write
        # here. /JTO 19/5/2019
        if not self.user_options.shiftedmetric:
            addFromRegions('sinty')
        addFromRegions('g11')
        addFromRegions('g22')
        addFromRegions('g33')
        addFromRegions('g12')
        addFromRegions('g13')
        addFromRegions('g23')
        addFromRegions('J')
        addFromRegions('g_11')
        addFromRegions('g_22')
        addFromRegions('g_33')
        addFromRegions('g_12')
        addFromRegions('g_13')
        addFromRegions('g_23')
        addFromRegions('curl_bOverB_x')
        addFromRegions('curl_bOverB_y')
        addFromRegions('curl_bOverB_z')
        addFromRegions('bxcvx')
        addFromRegions('bxcvy')
        addFromRegions('bxcvz')

    def writeArray(self, name, array, f):
        f.write(name, BoutArray(array.centre, attributes=array.attributes))
        f.write(name+'_ylow', BoutArray(array.ylow[:, :-1], attributes=array.attributes))

    def writeGridfile(self, filename):
        from boututils.datafile import DataFile

        with DataFile(filename, create=True, format='NETCDF4') as f:
            f.write('nx', self.nx)
            # ny for BOUT++ excludes boundary guard cells
            f.write('ny', self.ny_noguards)
            f.write('y_boundary_guards', self.user_options.y_boundary_guards)
            f.write('curvature_type', self.user_options.curvature_type)
            f.write('Bt_axis', self.equilibrium.Bt_axis)

            # write the 2d fields
            for name in self.fields_to_output:
                self.writeArray(name, self.__dict__[name], f)

            # Write topology-setting indices for BoutMesh
            eq_region0 = next(iter(self.equilibrium.regions.values()))
            if len(self.x_startinds) == 1:
                # No separatrix in grid
                if eq_region0.separatrix_radial_index == 0:
                    # SOL only
                    ixseps1 = -1
                    ixseps2 = -1
                else:
                    # core only
                    ixseps1 = self.nx
                    ixseps2 = self.nx
            elif len(self.x_startinds) == 2:
                # One separatrix
                ixseps1 = self.x_startinds[1]
                ixseps2 = self.nx # note: this may be changed below for cases where the two separatrices are in the same radial location
            elif len(self.x_startinds) == 3:
                # Two separatrices
                ixseps1 = self.x_startinds[1]
                ixseps2 = self.x_startinds[2]
            else:
                raise ValueError('More than two separatrices not supported by BoutMesh')

            if len(self.y_regions_noguards) == 1:
                # No X-points
                jyseps1_1 = -1
                jyseps2_1 = self.ny//2
                ny_inner = self.ny//2
                jyseps1_2 = self.ny//2
                jyseps2_2 = self.ny
            elif len(self.y_regions_noguards) == 2:
                raise ValueError('Unrecognized topology with 2 y-regions')
            elif len(self.y_regions_noguards) == 3:
                # single-null
                jyseps1_1 = self.y_regions_noguards[0] - 1
                jyseps2_1 = self.ny//2
                ny_inner = self.ny//2
                jyseps1_2 = self.ny//2
                jyseps2_2 = sum(self.y_regions_noguards[:2]) - 1
            elif len(self.y_regions_noguards) == 4:
                # single X-point with all 4 legs ending on walls
                jyseps1_1 = self.y_regions_noguards[0] - 1
                jyseps2_1 = jyseps1_1
                ny_inner = sum(self.y_regions_noguards[:2])
                jyseps2_2 = sum(self.y_regions_noguards[:3]) - 1
                jyseps1_2 = jyseps2_2

                # for BoutMesh topology, this is equivalent to 2 X-points on top of each
                # other, so there are 2 separatrices, in the same radial location
                ixseps2 = ixseps1
            elif len(self.y_regions_noguards) == 5:
                raise ValueError('Unrecognized topology with 5 y-regions')
            elif len(self.y_regions_noguards) == 6:
                # double-null
                jyseps1_1 = self.y_regions_noguards[0] - 1
                jyseps2_1 = sum(self.y_regions_noguards[:2]) - 1
                ny_inner = sum(self.y_regions_noguards[:3])
                jyseps1_2 = sum(self.y_regions_noguards[:4]) - 1
                jyseps2_2 = sum(self.y_regions_noguards[:5]) - 1

                if ixseps2 == self.nx:
                    # this is a connected-double-null configuration, with two separatrices
                    # in the same radial location
                    ixseps2 = ixseps1

            f.write('ixseps1', ixseps1)
            f.write('ixseps2', ixseps2)
            f.write('jyseps1_1', jyseps1_1)
            f.write('jyseps2_1', jyseps2_1)
            f.write('ny_inner', ny_inner)
            f.write('jyseps1_2', jyseps1_2)
            f.write('jyseps2_2', jyseps2_2)

            # BOUT++ ParallelTransform that metrics are compatible with
            if self.user_options.shiftedmetric:
                # Toroidal coordinates with shifts to calculate parallel derivatives
                f.write('parallel_transform', 'shiftedmetric')
            else:
                # Field-aligned coordinates
                f.write('parallel_transform', 'identity')

            f.write('hypnotoad_inputs', self.equilibrium._getOptionsAsString())
            f.write('hypnotoad_git_hash', self.git_hash)
            f.write('hypnotoad_git_diff', self.git_diff)

    def plot2D(self, f, title=None):
        from matplotlib import pyplot

        try:
            vmin = f.min()
            vmax = f.max()
            if vmin == vmax:
                vmin -= 0.1
                vmax += 0.1

            for region, indices in zip(self.regions.values(), self.region_indices.values()):
                pyplot.pcolor(region.Rxy.corners, region.Zxy.corners, f[indices],
                              vmin=vmin, vmax=vmax)

            pyplot.colorbar()
        except NameError:
            raise NameError('Some variable has not been defined yet: have you called Mesh.geometry()?')

    def saveOptions(self, filename='hypnotoad_options.yaml'):
        self.equilibrium.saveOptions(filename)
