# Copyright 2019 J.T. Omotani
#
# Contact John Omotani john.omotani@ukaea.uk
#
# This file is part of Hypnotoad 2.
#
# Hypnotoad 2 is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Hypnotoad 2 is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# Hypnotoad 2.  If not, see <http://www.gnu.org/licenses/>.

"""
Functions for analysing an equilibrium for which an interpolating function is given for
the potential.
"""

from collections import OrderedDict
from copy import deepcopy
import warnings

import numpy
from options import Options
from scipy.optimize import minimize_scalar, brentq
from scipy.interpolate import interp1d
from scipy.integrate import solve_ivp

from ..utils.hypnotoad_options import HypnotoadInternalOptions


class SolutionError(Exception):
    """
    Solution was not found
    """

    pass


# tolerance used to try and avoid missed intersections between lines
# also if two sets of lines appear to intersect twice, only count it once if the
# distance between the intersections is less than this
intersect_tolerance = 1.0e-14


def setDefault(options, name, default):
    if options[name] is None:
        options[name] = default
    return options[name]


class Point2D:
    """
    A point in 2d space.
    Can be added, subtracted, multiplied by scalar
    """

    def __init__(self, R, Z):
        self.R = R
        self.Z = Z

    def __add__(self, other):
        return Point2D(self.R + other.R, self.Z + other.Z)

    def __sub__(self, other):
        return Point2D(self.R - other.R, self.Z - other.Z)

    def __mul__(self, other):
        return Point2D(self.R * other, self.Z * other)

    def __rmul__(self, other):
        return Point2D(self.R * other, self.Z * other)

    def __truediv__(self, other):
        return Point2D(self.R / other, self.Z / other)

    def __iter__(self):
        """
        Along with __next__() allows Point2D class to be treated like a tuple, e.g.
        p = Point2D(1., 0.)
        val = f(*p)
        where f is a function that takes two arguments
        """
        self.iterStep = 0
        return self

    def __next__(self):
        if self.iterStep == 0:
            self.iterStep = 1
            return self.R
        elif self.iterStep == 1:
            self.iterStep = 2
            return self.Z
        else:
            raise StopIteration

    def __repr__(self):
        """
        Allow Point2D to be printed
        """
        return "Point2D(" + str(self.R) + "," + str(self.Z) + ")"

    def as_ndarray(self):
        return numpy.array((self.R, self.Z))


def calc_distance(p1, p2):
    d = p2 - p1
    return numpy.sqrt(d.R ** 2 + d.Z ** 2)


def swap_points(p1, p2):
    tempR = p1.R
    tempZ = p1.Z
    p1.R = p2.R
    p1.Z = p2.Z
    p2.R = tempR
    p2.Z = tempZ


def find_intersections(l1array, l2start, l2end):
    """
    Find the intersection (if there is one) between the array of lines 'l1' and the line
    'l2'.
    """
    # Copy so we don't change the inputs
    l1array = l1array.copy()
    l2start = deepcopy(l2start)
    l2end = deepcopy(l2end)

    R1array = numpy.zeros([l1array.shape[0] - 1, 2])
    R1array[:, 0] = l1array[:-1, 0]
    R1array[:, 1] = l1array[1:, 0]
    Z1array = numpy.zeros([l1array.shape[0] - 1, 2])
    Z1array[:, 0] = l1array[:-1, 1]
    Z1array[:, 1] = l1array[1:, 1]

    # for inds1, if l1 is sensible, dR1 shouldn't be too small as it's bigger than dZ1
    # l1 is Z = Z1 + dZ1/dR1 * (R - R1)
    # If the lines are parallel
    inds_a = numpy.where(
        numpy.abs(R1array[:, 0] - R1array[:, 1])
        > numpy.abs(Z1array[:, 0] - Z1array[:, 1])
    )[0]
    thisR1_a = R1array[inds_a, :]
    thisZ1_a = Z1array[inds_a, :]

    # sort inds_a points in R
    sortinds = numpy.argsort(thisR1_a, axis=1)
    na = thisR1_a.shape[0]
    thisR1_a = thisR1_a[numpy.arange(na)[:, numpy.newaxis], sortinds]
    thisZ1_a = thisZ1_a[numpy.arange(na)[:, numpy.newaxis], sortinds]

    # if l2 is sensible, dZ2 shouldn't be too small as it's bigger than dR2
    # l2 is R = R2 + dR2/dZ2 * (Z - Z2)
    inds_b = numpy.where(
        numpy.abs(R1array[:, 0] - R1array[:, 1])
        <= numpy.abs(Z1array[:, 0] - Z1array[:, 1])
    )[0]

    thisR1_b = R1array[inds_b, :]
    thisZ1_b = Z1array[inds_b, :]

    # sort inds_b points in Z
    sortinds = numpy.argsort(thisZ1_b, axis=1)
    nb = thisR1_b.shape[0]
    thisR1_b = thisR1_b[numpy.arange(nb)[:, numpy.newaxis], sortinds]
    thisZ1_b = thisZ1_b[numpy.arange(nb)[:, numpy.newaxis], sortinds]

    if numpy.abs(l2end.R - l2start.R) > numpy.abs(l2end.Z - l2start.Z):
        # if l2 is sensible, dR2 shouldn't be too small as it's bigger than dZ2
        # l2 is Z = Z2 + dZ2/dR2 * (R - R2)

        # sort l2 points in R
        if l2start.R > l2end.R:
            swap_points(l2start, l2end)
        R2 = l2start.R
        Z2 = l2start.Z
        dR2 = l2end.R - l2start.R
        dZ2 = l2end.Z - l2start.Z

        # Check intersections with 'a' lines
        #
        # If this condition is not true, lines are parallel so cannot intersect
        condition = numpy.where(
            numpy.abs(
                (thisZ1_a[:, 1] - thisZ1_a[:, 0]) / (thisR1_a[:, 1] - thisR1_a[:, 0])
                - dZ2 / dR2
            )
            >= 1.0e-15
        )
        inds_a = inds_a[condition]
        thisR1_a = thisR1_a[condition]
        thisZ1_a = thisZ1_a[condition]

        thisdR1 = thisR1_a[:, 1] - thisR1_a[:, 0]
        thisdZ1 = thisZ1_a[:, 1] - thisZ1_a[:, 0]

        # intersection where
        # Z1 + dZ1/dR1 * (R - R1) = Z2 + dZ2/dR2 * (R - R2)
        # (dZ1/dR1 - dZ2/dR2)*R = Z2 - Z1 + dZ1/dR1*R1 - dZ2/dR2*R2
        Rcross = (
            Z2 - thisZ1_a[:, 0] + thisdZ1 / thisdR1 * thisR1_a[:, 0] - dZ2 / dR2 * R2
        ) / (thisdZ1 / thisdR1 - dZ2 / dR2)
        intersect_inds = numpy.where(
            numpy.logical_and(
                Rcross >= thisR1_a[:, 0] - intersect_tolerance,
                numpy.logical_and(
                    Rcross <= thisR1_a[:, 1] + intersect_tolerance,
                    numpy.logical_and(
                        Rcross >= R2 - intersect_tolerance,
                        Rcross <= l2end.R + intersect_tolerance,
                    ),
                ),
            )
        )
        Rintersect_a = Rcross[intersect_inds]
        Zintersect_a = thisZ1_a[:, 0][intersect_inds] + thisdZ1[
            intersect_inds
        ] / thisdR1[intersect_inds] * (Rintersect_a - thisR1_a[:, 0][intersect_inds])

        # Check intersections with 'b' lines
        #
        thisdR1 = thisR1_b[:, 1] - thisR1_b[:, 0]
        thisdZ1 = thisZ1_b[:, 1] - thisZ1_b[:, 0]

        # intersection where
        # R = R1 + dR1/dZ1 * (Z2 + dZ2/dR2 * (R - R2) - Z1)
        # (1 - dR1/dZ1*dZ2/dR2) * R = R1 + dR1/dZ1 * (Z2 - dZ2/dR2*R2 - Z1)
        Rcross = (
            thisR1_b[:, 0] + thisdR1 / thisdZ1 * (Z2 - dZ2 / dR2 * R2 - thisZ1_b[:, 0])
        ) / (1.0 - thisdR1 / thisdZ1 * dZ2 / dR2)
        Zcross = Z2 + dZ2 / dR2 * (Rcross - R2)
        intersect_inds = numpy.where(
            numpy.logical_and(
                Zcross >= thisZ1_b[:, 0] - intersect_tolerance,
                numpy.logical_and(
                    Zcross <= thisZ1_b[:, 1] + intersect_tolerance,
                    numpy.logical_and(
                        Rcross >= R2 - intersect_tolerance,
                        Rcross <= l2end.R + intersect_tolerance,
                    ),
                ),
            )
        )
        Rintersect_b = Rcross[intersect_inds]
        Zintersect_b = Zcross[intersect_inds]
    else:
        # if l2 is sensible, dZ2 shouldn't be too small as it's bigger than dR2
        # l2 is R = R2 + dR2/dZ2 * (Z - Z2)

        # sort l2 points in Z
        if l2start.Z > l2end.Z:
            swap_points(l2start, l2end)
        R2 = l2start.R
        Z2 = l2start.Z
        dR2 = l2end.R - l2start.R
        dZ2 = l2end.Z - l2start.Z

        # Check intersections with 'a' lines
        #
        thisdR1 = thisR1_a[:, 1] - thisR1_a[:, 0]
        thisdZ1 = thisZ1_a[:, 1] - thisZ1_a[:, 0]

        # intersection where
        # Z = Z1 + dZ1/dR1 * (R2 + dR2/dZ2 * (Z - Z2) - R1)
        # (1 - dZ1*dR2/dR1/dZ2) * Z = Z1 + dZ1/dR1 * (R2 - dR2/dZ2*Z2 - R1)
        Zcross = (
            thisZ1_a[:, 0] + thisdZ1 / thisdR1 * (R2 - dR2 / dZ2 * Z2 - thisR1_a[:, 0])
        ) / (1.0 - thisdZ1 * dR2 / (thisdR1 * dZ2))
        Rcross = R2 + dR2 / dZ2 * (Zcross - Z2)
        intersect_inds = numpy.where(
            numpy.logical_and(
                Rcross >= thisR1_a[:, 0] - intersect_tolerance,
                numpy.logical_and(
                    Rcross <= thisR1_a[:, 1] + intersect_tolerance,
                    numpy.logical_and(
                        Zcross >= Z2 - intersect_tolerance,
                        Zcross <= l2end.Z + intersect_tolerance,
                    ),
                ),
            )
        )
        Rintersect_a = Rcross[intersect_inds]
        Zintersect_a = Zcross[intersect_inds]

        # Check intersections with 'b' lines
        #
        # If this condition is not true, lines are parallel so cannot intersect
        condition = numpy.where(
            numpy.abs(
                dR2 / dZ2
                - (thisR1_b[:, 1] - thisR1_b[:, 0]) / (thisZ1_b[:, 1] - thisZ1_b[:, 0])
            )
            >= 1.0e-15
        )
        inds_b = inds_b[condition]
        thisR1_b = thisR1_b[condition]
        thisZ1_b = thisZ1_b[condition]

        thisdR1 = thisR1_b[:, 1] - thisR1_b[:, 0]
        thisdZ1 = thisZ1_b[:, 1] - thisZ1_b[:, 0]

        # intersection where
        # R2 + dR2/dZ2 * (Z - Z2) = R1 + dR1/dZ1 * (Z - Z1)
        # (dR2/dZ2 - dR1*dZ1) * Z = R1 - R2 + dR2/dZ2*Z2 - dR1/dZ1*Z1
        Zcross = (
            thisR1_b[:, 0] - R2 + dR2 / dZ2 * Z2 - thisdR1 / thisdZ1 * thisZ1_b[:, 0]
        ) / (dR2 / dZ2 - thisdR1 / thisdZ1)
        intersect_inds = numpy.where(
            numpy.logical_and(
                Zcross >= thisZ1_b[:, 0] - intersect_tolerance,
                numpy.logical_and(
                    Zcross <= thisZ1_b[:, 1] + intersect_tolerance,
                    numpy.logical_and(
                        Zcross >= Z2 - intersect_tolerance,
                        Zcross <= l2end.Z + intersect_tolerance,
                    ),
                ),
            )
        )
        Zintersect_b = Zcross[intersect_inds]
        Rintersect_b = R2 + dR2 / dZ2 * (Zintersect_b - Z2)

    Rintersect = numpy.concatenate([Rintersect_a, Rintersect_b])
    Zintersect = numpy.concatenate([Zintersect_a, Zintersect_b])

    if len(Rintersect) > 0 or len(Zintersect) > 0:
        return numpy.stack([Rintersect, Zintersect], axis=1)
    else:
        return None


class FineContour:
    """
    Used to give a high-resolution representation of a contour.
    Points in FineContour are uniformly spaced in poloidal distance along the contour.
    """

    options = Options(
        finecontour_Nfine=None,
        finecontour_atol=None,
        finecontour_diagnose=None,
        finecontour_maxits=None,
    )

    def __init__(self, parentContour):
        self.parentContour = parentContour
        self.distance = None
        Nfine = self.options.finecontour_Nfine

        endInd = self.parentContour.endInd
        if endInd < 0:
            # endInd might be negative, which would mean relative to the end of the list,
            # but we need the actual index below
            endInd += len(self.parentContour)
        n_input = endInd - self.parentContour.startInd + 1

        # Extend further than will be needed in the final contour, because extrapolation
        # past the end of the fine contour is very bad.
        self.extend_lower_fine = (
            2 * (self.parentContour.extend_lower * Nfine) // n_input
        )
        self.extend_upper_fine = (
            2 * (self.parentContour.extend_upper * Nfine) // n_input
        )

        self.indices_fine = numpy.linspace(
            -self.extend_lower_fine,
            (Nfine - 1 + self.extend_upper_fine),
            Nfine + self.extend_lower_fine + self.extend_upper_fine,
        )

        # Initial guess from interpolation of psiContour, iterate to a more accurate
        # version below.
        # Extend a copy of parentContour to make the extrapolation more stable.
        # This makes parentCopy have twice the extra points as parentContour has.
        parentCopy = self.parentContour.newContourFromSelf()
        parentCopy.temporaryExtend(
            extend_lower=self.parentContour.extend_lower,
            extend_upper=self.parentContour.extend_upper,
            ds_lower=calc_distance(parentCopy[0], parentCopy[1]),
            ds_upper=calc_distance(parentCopy[-1], parentCopy[-2]),
        )
        interp_input, distance_estimate = parentCopy._coarseInterp()

        sfine = distance_estimate[parentCopy.endInd] / (Nfine - 1) * self.indices_fine

        # 2d array with size {N,2} giving the (R,Z)-positions of points on the contour
        self.positions = numpy.array(tuple(interp_input(s).as_ndarray() for s in sfine))

        self.startInd = self.extend_lower_fine
        self.endInd = Nfine - 1 + self.extend_lower_fine

        self.equaliseSpacing()

    def extend(self, *, extend_lower=0, extend_upper=0):

        Nfine = self.options.finecontour_Nfine

        parentCopy = self.parentContour.newContourFromSelf()

        new_positions = numpy.zeros(
            [self.positions.shape[0] + extend_lower + extend_upper, 2]
        )

        if extend_upper == 0:
            new_positions[extend_lower:] = self.positions
        else:
            new_positions[extend_lower:-extend_upper] = self.positions

        if extend_lower != 0:
            self.extend_lower_fine += extend_lower

            ds_lower = self.distance[1] - self.distance[0]

            # distances from the first point in the FineContour to put initial guesses
            # for new points
            new_s_lower = numpy.arange(-extend_lower, 0.0) * ds_lower

            # Extend parentCopy to cover range of new_s_lower.
            ds_coarse = calc_distance(parentCopy[0], parentCopy[1])
            coarse_extend = int(extend_lower * ds_lower / ds_coarse)
            parentCopy.temporaryExtend(extend_lower=coarse_extend, ds_lower=ds_coarse)

            # Make sure parentCopy has point at start of existing FineContour - then
            # measure distances where initial guesses for new points are inserted
            # relative to that point, ensures points in new_positions are in the right
            # order
            first_point = Point2D(*self.positions[0, :])
            reference_ind = parentCopy.insertFindPosition(first_point)

            extrap_coarse = parentCopy._coarseExtrapLower(reference_ind)

            new_positions[:extend_lower, :] = [
                tuple(extrap_coarse(s)) for s in new_s_lower
            ]

        if extend_upper != 0:
            self.extend_upper_fine += extend_upper

            ds_upper = self.distance[-1] - self.distance[-2]

            # distances from the last point in the FineContour to put initial guesses for
            # new points
            new_s_upper = numpy.arange(1.0, extend_upper + 1) * ds_upper

            # Extend parentCopy to cover range of new_s_upper.
            ds_coarse = calc_distance(parentCopy[-2], parentCopy[-1])
            coarse_extend = int(extend_upper * ds_upper / ds_coarse)
            parentCopy.temporaryExtend(extend_upper=coarse_extend, ds_upper=ds_coarse)

            # Make sure parentCopy has point at end of existing FineContour - then
            # measure distances where initial guesses for new points are inserted
            # relative to that point, ensures points in new_positions are in the right
            # order
            last_point = Point2D(*self.positions[-1, :])
            reference_ind = parentCopy.insertFindPosition(last_point)

            extrap_coarse = parentCopy._coarseExtrapUpper(reference_ind)

            new_positions[-extend_upper:, :] = [
                tuple(extrap_coarse(s)) for s in new_s_upper
            ]

        self.positions = new_positions

        self.indices_fine = numpy.linspace(
            -self.extend_lower_fine,
            (Nfine - 1 + self.extend_upper_fine),
            Nfine + self.extend_lower_fine + self.extend_upper_fine,
        )

        self.startInd = self.extend_lower_fine
        self.endInd = Nfine - 1 + self.extend_lower_fine

        self.equaliseSpacing(reallocate=True)

    def equaliseSpacing(self, *, reallocate=False):
        """
        Adjust the positions of points in this FineContour so they have a constant
        distance between them.
        """

        self.refine()

        self.calcDistance(reallocate=reallocate)

        ds = self.distance[1:] - self.distance[:-1]
        # want constant spacing, so ds has a constant value
        ds_mean = numpy.mean(ds)
        # maximum error
        ds_error = numpy.max(numpy.sqrt((ds - ds_mean) ** 2))

        if FineContour.options.finecontour_diagnose:
            from matplotlib import pyplot

            print("diagnosing FineContour.__init__()")
            print("extend_lower_fine", self.extend_lower_fine)
            print("extend_upper_fine", self.extend_upper_fine)
            print("ds_error", ds_error)

            Rpoints = self.positions[:, 0]
            Zpoints = self.positions[:, 1]
            R = numpy.linspace(Rpoints.min(), Rpoints.max(), 100)
            Z = numpy.linspace(Zpoints.min(), Zpoints.max(), 100)

            pyplot.figure()

            pyplot.subplot(131)
            pyplot.contour(
                R, Z, self.parentContour.psi(R[numpy.newaxis, :], Z[:, numpy.newaxis])
            )
            pyplot.plot(Rpoints, Zpoints, marker="x")
            pyplot.xlabel("R")
            pyplot.ylabel("Z")

            pyplot.subplot(132)
            pyplot.plot(ds)
            pyplot.ylabel("ds")

            pyplot.subplot(133)
            pyplot.plot(Rpoints, label="R")
            pyplot.plot(Zpoints, label="Z")
            pyplot.xlabel("index")
            pyplot.legend()
            pyplot.show()

        count = 1
        while ds_error > self.options.finecontour_atol:

            if (
                self.options.finecontour_maxits
                and count > self.options.finecontour_maxits
            ):
                warnings.warn(
                    f"FineContour: maximum iterations "
                    f"({self.options.finecontour_maxits}) exceeded with ds_error "
                    f"{ds_error}"
                )
                break

            sfine = (
                self.totalDistance()
                / (self.options.finecontour_Nfine - 1)
                * self.indices_fine
            )

            interpFunc = self.interpFunction()

            # 2d array with size {N,2} giving the (R,Z)-positions of points on the
            # contour
            self.positions = numpy.array(
                tuple(interpFunc(s).as_ndarray() for s in sfine)
            )

            self.refine()

            self.calcDistance()

            ds = self.distance[1:] - self.distance[:-1]
            # want constant spacing, so ds has a constant value
            ds_mean = numpy.mean(ds)
            # maximum error
            ds_error = numpy.max(numpy.sqrt((ds - ds_mean) ** 2))

            count += 1

            if FineContour.options.finecontour_diagnose:
                print("iteration", count, "  ds_error", ds_error)

                Rpoints = self.positions[:, 0]
                Zpoints = self.positions[:, 1]
                R = numpy.linspace(Rpoints.min(), Rpoints.max(), 100)
                Z = numpy.linspace(Zpoints.min(), Zpoints.max(), 100)

                pyplot.figure()

                pyplot.subplot(131)
                pyplot.contour(
                    R,
                    Z,
                    self.parentContour.psi(R[numpy.newaxis, :], Z[:, numpy.newaxis]),
                )
                pyplot.plot(Rpoints, Zpoints, marker="x")
                pyplot.xlabel("R")
                pyplot.ylabel("Z")

                pyplot.subplot(132)
                pyplot.plot(ds)
                pyplot.ylabel("ds")

                pyplot.subplot(133)
                pyplot.plot(Rpoints, label="R")
                pyplot.plot(Zpoints, label="Z")
                pyplot.xlabel("index")
                pyplot.legend()
                pyplot.show()

    def totalDistance(self):
        return self.distance[self.endInd] - self.distance[self.startInd]

    def calcDistance(self, *, reallocate=False):
        if self.distance is None or reallocate:
            self.distance = numpy.zeros(self.positions.shape[0])
        deltaSquared = (self.positions[1:] - self.positions[:-1]) ** 2
        self.distance[1:] = numpy.cumsum(numpy.sqrt(numpy.sum(deltaSquared, axis=1)))

    def interpFunction(self, *, kind="cubic"):
        distance = self.distance - self.distance[self.startInd]

        interpR = interp1d(
            distance,
            self.positions[:, 0],
            kind=kind,
            assume_sorted=True,
            fill_value="extrapolate",
        )
        interpZ = interp1d(
            distance,
            self.positions[:, 1],
            kind=kind,
            assume_sorted=True,
            fill_value="extrapolate",
        )
        return lambda s: Point2D(float(interpR(s)), float(interpZ(s)))

    def refine(self):
        result = numpy.zeros(self.positions.shape)

        p = self.positions[0, :]
        tangent = self.positions[1, :] - self.positions[0, :]
        result[0, :] = self.parentContour.refinePoint(
            Point2D(*p), Point2D(*tangent)
        ).as_ndarray()
        for i in range(1, self.positions.shape[0] - 1):
            p = self.positions[i, :]
            tangent = self.positions[i + 1, :] - self.positions[i - 1, :]
            result[i, :] = self.parentContour.refinePoint(
                Point2D(*p), Point2D(*tangent)
            ).as_ndarray()
        p = self.positions[-1, :]
        tangent = self.positions[-1, :] - self.positions[-2, :]
        result[-1, :] = self.parentContour.refinePoint(
            Point2D(*p), Point2D(*tangent)
        ).as_ndarray()

        self.positions = result

    def reverse(self):
        if self.distance is not None:
            self.distance = self.distance[-1] - self.distance[::-1]
        self.positions = self.positions[::-1, :]

        old_start = self.startInd
        n = self.positions.shape[0]
        self.startInd = n - 1 - self.endInd
        self.endInd = n - 1 - old_start

    def interpSSperp(self, vec, kind="cubic"):
        """
        Returns:
        1. a function s(s_perp) for interpolating the poloidal distance along the contour
           from the distance perpendicular to vec.
           's_perp' is modified to be a monotonically increasing function along the
           contour.
        2. the total perpendicular distance between startInd and endInd of the contour.
        """

        # vec_perp is a vector in the direction of either increasing or decreasing sperp
        vec_perp = numpy.zeros(2)
        vec_perp[0] = -vec[1]
        vec_perp[1] = vec[0]

        # make vec_perp a unit vector
        vec_perp = vec_perp / numpy.sqrt(numpy.sum(vec_perp ** 2))
        start_position = self.positions[self.startInd, :]

        # s_perp = (vec_perp).(r) where r is the displacement vector of each point from
        # self[self.startInd]
        s_perp = numpy.sum(
            (self.positions - start_position) * vec_perp[numpy.newaxis, :], axis=1
        )

        # s_perp might not be monotonic in which case s(s_perp) is not well defined.
        # To get around this, if d(s_perp) between two points is negative, flip its sign
        # to make a fake 's_perp' that is always increasing.
        # Note we only need s_perp to be good near one of the ends, the function using it
        # will be multiplied by a weight that goes to zero far from the end.
        # This correction means s_perp is always increasing, regardless of sign of
        # vec_perp, so don't need to check sign of vec_perp when creating it.
        for i in range(self.startInd + 1, len(s_perp)):
            ds = s_perp[i] - s_perp[i - 1]
            if ds < 0.0:
                s_perp[i:] = 2.0 * s_perp[i - 1] - s_perp[i:]
        for i in range(self.startInd - 1, -1, -1):
            ds = s_perp[i + 1] - s_perp[i]
            if ds < 0.0:
                s_perp[: i + 1] = 2.0 * s_perp[i + 1] - s_perp[: i + 1]

        s_perp_total = s_perp[self.endInd] - s_perp[self.startInd]

        distance = self.distance - self.distance[self.startInd]
        s_of_sperp = interp1d(
            s_perp, distance, kind=kind, assume_sorted=True, fill_value="extrapolate"
        )

        return s_of_sperp, s_perp_total

    def getDistance(self, p):
        """
        Return the distance of a point along the contour.
        Assume p is a point on the contour so has the correct psi-value.
        """
        p = p.as_ndarray()

        distance_from_points = numpy.sqrt(
            numpy.sum((self.positions - p[numpy.newaxis, :]) ** 2, axis=1)
        )

        # index of closest point
        i1 = numpy.argmin(distance_from_points)
        d1 = distance_from_points[i1]

        # index of next-closest point
        if i1 + 1 >= len(distance_from_points):
            i2 = i1 - 1
        elif i1 - 1 < 0:
            i2 = 1
        elif distance_from_points[i1 + 1] < distance_from_points[i1 - 1]:
            i2 = i1 + 1
        else:
            i2 = i1 - 1
        d2 = distance_from_points[i2]

        # linearly interpolate the distance of the two closest points in the same ratio
        # as their distances from the point
        r = d2 / (d1 + d2)

        return r * self.distance[i1] + (1.0 - r) * self.distance[i2]

    def plot(self, *args, plotPsi=False, **kwargs):
        from matplotlib import pyplot

        Rpoints = self.positions[:, 0]
        Zpoints = self.positions[:, 1]
        if plotPsi:
            R = numpy.linspace(min(Rpoints), max(Rpoints), 100)
            Z = numpy.linspace(min(Zpoints), max(Zpoints), 100)
            pyplot.contour(R, Z, self.psi(R[numpy.newaxis, :], Z[:, numpy.newaxis]))
        pyplot.plot(Rpoints, Zpoints, *args, **kwargs)


class PsiContour:
    """
    Represents a contour as a collection of points.
    Includes methods for interpolation.
    Mostly behaves like a list
    """

    options = Options(refine_width=1.0e-5, refine_atol=2.0e-8, refine_methods="line")

    def __init__(self, points, psi, psival):
        self.points = points

        self._startInd = 0
        self._endInd = len(points) - 1

        self._fine_contour = None

        self._distance = None

        # Function that evaluates the vector potential at R,Z
        self.psi = psi

        # Value of vector potential on this contour
        self.psival = psival

        # Number of boundary guard cells at either end
        # This may be set even if the contour has not been extended yet, to specify how
        # many guard cells should be added when it is - this is extra information to
        # startInd and endInd.
        self._extend_lower = 0
        self._extend_upper = 0

    @property
    def startInd(self):
        return self._startInd

    @startInd.setter
    def startInd(self, val):
        if self._startInd != val:
            # self._fine_contour needs to be recalculated if the start position changes
            self._fine_contour = None
            self._distance = None
            self._startInd = val

    @property
    def endInd(self):
        return self._endInd

    @endInd.setter
    def endInd(self, val):
        if self._endInd != val:
            # self._fine_contour needs to be recalculated if the end position changes
            self._fine_contour = None
            self._distance = None
            self._endInd = val

    @property
    def extend_lower(self):
        return self._extend_lower

    @extend_lower.setter
    def extend_lower(self, val):
        if self._extend_lower != val:
            # self._fine_contour needs to be recalculated if extend_lower changes, to add
            # more points at the lower end
            self._fine_contour = None
            self._extend_lower = val

    @property
    def extend_upper(self):
        return self._extend_upper

    @extend_upper.setter
    def extend_upper(self, val):
        if self._extend_upper != val:
            # self._fine_contour needs to be recalculated if extend_upper changes, to add
            # more points at the upper end
            self._fine_contour = None
            self._extend_upper = val

    @property
    def fine_contour(self):
        if self._fine_contour is None:
            self._fine_contour = FineContour(self)
        return self._fine_contour

    @property
    def distance(self):
        if self._distance is None:
            self._distance = [self.fine_contour.getDistance(p) for p in self]
        return self._distance

    def __iter__(self):
        return self.points.__iter__()

    def __str__(self):
        return self.points.__str__()

    def __getitem__(self, key):
        return self.points.__getitem__(key)

    def __len__(self):
        return self.points.__len__()

    def setSelfToContour(self, contour):
        """
        Copy the state of this object from contour
        """
        self.points = deepcopy(contour.points)
        self.startInd = contour.startInd
        self.endInd = contour.endInd
        self._distance = contour._distance
        self.psi = contour.psi
        self.psival = contour.psival
        self.extend_lower = contour.extend_lower
        self.extend_upper = contour.extend_upper
        self._fine_contour = contour._fine_contour

    def newContourFromSelf(self, *, points=None, psival=None):
        if points is None:
            points = deepcopy(self.points)
        if psival is None:
            psival = self.psival
        new_contour = PsiContour(points, self.psi, psival)

        new_contour.startInd = self.startInd
        new_contour.endInd = self.endInd
        new_contour.extend_lower = self.extend_lower
        new_contour.extend_upper = self.extend_upper
        if points is None:
            new_contour._fine_contour = self._fine_contour

        return new_contour

    def append(self, point):
        self._fine_contour = None
        self._distance = None
        self.points.append(point)

    def prepend(self, point):
        self._fine_contour = None
        self._distance = None
        self.points.insert(0, point)

    def insert(self, index, point):
        self._distance = None

        # Make sure index is positive, following behaviour of list.insert()
        if index < 0:
            index += len(self)
            if index < 0:
                index = 0

        self.points.insert(index, point)

        if index <= self.startInd:
            self.startInd += 1
        if index <= self.endInd:
            self.endInd += 1
        if self.endInd < 0 and index > len(self) + self.endInd:
            self.endInd -= 1

    def insertFindPosition(self, point):
        """
        Insert a point into the PsiContour, finding its position in the list. Input point
        should be on the correct psi-value already. If the point being inserted is very
        close to an existing point, do not insert and return the index of the existing
        point.

        Returns
        -------
        int
            index where the point was inserted.
        """
        d = [calc_distance(point, p) for p in self]
        minind = numpy.argmin(d)

        # check if point to be inserted is very close to existing point
        if calc_distance(point, self[minind]) < self.options.refine_atol:
            return minind

        if minind == 0 and d[1] > calc_distance(self[0], self[1]):
            self.prepend(point)
            return 0
        elif minind == 0:
            self.insert(1, point)
            return 1
        elif minind == len(self) - 1 and d[-2] > calc_distance(self[-1], self[-2]):
            self.append(point)
            return minind + 1
        elif minind == len(self) - 1:
            self.insert(minind, point)
            return minind
        elif d[minind - 1] > d[minind + 1]:
            self.insert(minind + 1, point)
            return minind + 1
        else:
            self.insert(minind, point)
            return minind

    def totalDistance(self):
        return self.distance[self.endInd] - self.distance[self.startInd]

    def reverse(self):
        self.points.reverse()
        old_start = self.startInd
        self.startInd = len(self) - 1 - self.endInd
        self.endInd = len(self) - 1 - old_start

        # reset distance - will be recalculated from self._fine_contour
        self._distance = None

        if self._fine_contour is not None:
            self._fine_contour.reverse()

    def refine(self, *args, **kwargs):
        new = self.getRefined(*args, **kwargs)
        self.points = new.points
        self._distance = new._distance

    def refinePointNewton(self, p, tangent, width, atol):
        """Use Newton iteration to refine point.
        This should converge quickly if the original point is sufficiently close
        """

        def f(s):
            return self.psi(*(p + s * tangent)) - self.psival

        def dfds(s, eps=1e-10):
            return (f(s + eps) - f(s)) / eps

        fprev = f(0.0)

        if numpy.abs(fprev) < atol * numpy.abs(self.psival):
            # don't need to refine
            return p

        attempts = [(0.0, fprev, -1)]

        fnext = 0.0
        s = 0.0
        count = 0
        while True:
            # Take another iteration
            s -= fprev / dfds(s)
            fnext = f(s)
            attempts.append((count, s, fnext))
            if abs(fnext) < atol:
                # Converged
                return p + s * tangent
            if abs(fnext) > abs(fprev) or count > 10:
                raise SolutionError("Diverging newton iteration")
            count += 1
            fprev = fnext

    def refinePointLinesearch(self, p, tangent, width, atol):
        """Refines the location of a point p, using a line search method
        along the tangent vector
        """

        def f(R, Z):
            return self.psi(R, Z) - self.psival

        if numpy.abs(f(*p)) < atol * numpy.abs(self.psival):
            # don't need to refine
            return p

        def perpLine(w):
            # p - point through which to draw perpLine
            # tangent - vector tangent to original curve, result will be perpendicular to
            #           this
            # w - width on either side of p to draw the perpLine to
            modTangent = numpy.sqrt(tangent.R ** 2 + tangent.Z ** 2)
            perpIdentityVector = Point2D(
                tangent.Z / modTangent, -tangent.R / modTangent
            )
            return lambda s: p + 2.0 * (s - 0.5) * w * perpIdentityVector

        w = width
        while True:
            try:
                pline = perpLine(w)
                snew, info = brentq(
                    lambda s: f(*pline(s)), 0.0, 1.0, xtol=atol, full_output=True
                )
                if info.converged:
                    return pline(snew)

            except ValueError:
                pass
            w /= 2.0
            if w < atol:
                if False:
                    print("width =", width)
                    print("p = ", p)
                    print("psi = {}, psival = {}".format(self.psi(*p), self.psival))
                    print("Range: {} -> {}".format(f(*pline(0.0)), f(*pline(1.0))))

                    pline0 = perpLine(width)
                    Rbox = numpy.linspace(p.R - 0.1, p.R + 0.1, 100)[numpy.newaxis, :]
                    Zbox = numpy.linspace(p.Z - 0.1, p.Z + 0.1, 100)[:, numpy.newaxis]
                    svals = numpy.linspace(0.0, 1.0, 40)

                    from matplotlib import pyplot

                    pyplot.figure()
                    self.plot("+")
                    pyplot.contour(
                        Rbox + 0.0 * Zbox, Zbox + 0.0 * Rbox, self.psi(Rbox, Zbox), 200
                    )
                    pyplot.plot(
                        [pline0(s).R for s in svals], [pline0(s).Z for s in svals], "x"
                    )
                    pyplot.figure()
                    pyplot.plot([f(*pline0(s)) for s in svals])
                    pyplot.show()
                raise SolutionError(
                    "Could not find interval to refine point at " + str(p)
                )

    def refinePointIntegrate(self, p, tangent, width, atol):
        """Integrates across flux surfaces from p

        Integrates this:
        dR/dpsi = dpsi/dR / ((dpsi/dZ)**2 + (dpsi/dR)**2)
        dZ/dpsi = dpsi/dZ / ((dpsi/dZ)**2 + (dpsi/dR)**2)

        Note: This is the method used in the original Hypnotoad
        """

        def func(psi, position, eps=1e-10):
            R = position[0]
            Z = position[1]
            psi0 = self.psi(R, Z)  # Note: This should be close to psi
            # Calculate derivatives using finite difference
            dpsidr = (self.psi(R + eps, Z) - psi0) / eps
            dpsidz = (self.psi(R, Z + eps) - psi0) / eps
            norm = 1.0 / (dpsidr ** 2 + dpsidz ** 2)  # Common factor
            return [dpsidr * norm, dpsidz * norm]

        result = solve_ivp(
            func, (self.psi(*p), self.psival), [p.R, p.Z]  # Range of psi
        )  # Starting location
        if not result.success:
            raise SolutionError("refinePointIntegrate failed to converge")
        return Point2D(*result.y[:, 1])

    def refinePoint(self, p, tangent, width=None, atol=None, methods=None):
        """Starting from point p, find a nearby point where
        self.psi(p) is close to self.psival, by moving along
        the tangent vector.

        methods   A comma-separated list of methods to use.
                  This overrides options.refine_methods

                  Valid names are:
                  - "newton"       Newton iteration
                  - "line"         A line search
                  - "integrate"    Integrate along psi gradient
                  - "integrate+newton"  Integrate, then refine with Newton
                  - "none"         No refinement (always succeeds)

        If all the methods specified fail, a SolutionError is raised.

        """

        if self.psival is None:
            # Can't refine
            return p

        # Available methods. Note: Currently this selection
        # is done for every point. This would be better done once
        # during __init__ and then re-used.
        available_methods = {
            "newton": self.refinePointNewton,
            "line": self.refinePointLinesearch,
            "integrate": self.refinePointIntegrate,
            "integrate+newton": (
                lambda p, tangent, width, atol: self.refinePointNewton(
                    self.refinePointIntegrate(p, tangent, width, atol),
                    tangent,
                    width,
                    atol,
                )
            ),
            "none": lambda p, tangent, width, atol: p,
        }

        if width is None:
            width = PsiContour.options.refine_width
        if atol is None:
            atol = PsiContour.options.refine_atol

        assert width is not None
        assert atol is not None

        if methods is None:
            methods = PsiContour.options.refine_methods
            if methods is None:
                methods = "line"  # For now, original method

        for method in methods.split(","):
            try:
                # Try each method
                return available_methods[method.strip()](p, tangent, width, atol)
            except SolutionError:
                # If it fails, try the next one
                pass

        # All methods failed. If the user wants to continue anyway,
        # the last method in the methods list can be set to "none"
        raise SolutionError("refinePoint failed to converge with methods: " + methods)

    def getRefined(self, **kwargs):
        newpoints = []
        newpoints.append(
            self.refinePoint(self.points[0], self.points[1] - self.points[0], **kwargs)
        )
        for i, p in enumerate(self.points[1:-1]):
            # note i+1 here is the index of point p
            newpoints.append(
                self.refinePoint(p, self.points[i + 2] - self.points[i], **kwargs)
            )
        newpoints.append(
            self.refinePoint(
                self.points[-1], self.points[-1] - self.points[-2], **kwargs
            )
        )

        return self.newContourFromSelf(points=newpoints)

    def interpFunction(self):
        return self.fine_contour.interpFunction()

    def _coarseInterp(self, *, kind="cubic"):
        distance = [0.0]
        for i in range(len(self) - 1):
            distance.append(distance[i] + calc_distance(self[i + 1], self[i]))
        distance = numpy.array(numpy.float64(distance)) - distance[self.startInd]

        R = numpy.array(numpy.float64([p.R for p in self.points]))
        Z = numpy.array(numpy.float64([p.Z for p in self.points]))

        interpR = interp1d(
            distance, R, kind=kind, assume_sorted=True, fill_value="extrapolate"
        )
        interpZ = interp1d(
            distance, Z, kind=kind, assume_sorted=True, fill_value="extrapolate"
        )
        return lambda s: Point2D(interpR(s), interpZ(s)), distance

    def _coarseExtrapLower(self, reference_ind, *, kind="cubic"):
        """
        Returns an interpolation/extrapolation function for points near the beginning of
        this PsiContour, with distances relative to the point at 'reference_ind'.
        """

        npoints = reference_ind + 4

        distance = [0.0]
        for i in range(npoints - 1):
            distance.append(distance[i] + calc_distance(self[i + 1], self[i]))
        distance = numpy.array(numpy.float64(distance)) - distance[reference_ind]

        R = numpy.array(numpy.float64([p.R for p in self.points[:npoints]]))
        Z = numpy.array(numpy.float64([p.Z for p in self.points[:npoints]]))

        interpR = interp1d(
            distance, R, kind=kind, assume_sorted=True, fill_value="extrapolate"
        )
        interpZ = interp1d(
            distance, Z, kind=kind, assume_sorted=True, fill_value="extrapolate"
        )
        return lambda s: Point2D(interpR(s), interpZ(s))

    def _coarseExtrapUpper(self, reference_ind, *, kind="cubic"):
        """
        Returns an interpolation/extrapolation function for points near the beginning of
        this PsiContour, with distances relative to the point at 'reference_ind'.
        """

        if reference_ind < 0:
            reference_ind += len(self)

        npoints = (len(self) - 1 - reference_ind) + 4

        distance = [0.0]
        for i in range(reference_ind - 3, len(self) - 1):
            distance.append(distance[-1] + calc_distance(self[i + 1], self[i]))
        distance = numpy.array(numpy.float64(distance)) - distance[3]

        R = numpy.array(numpy.float64([p.R for p in self.points[-npoints:]]))
        Z = numpy.array(numpy.float64([p.Z for p in self.points[-npoints:]]))

        interpR = interp1d(
            distance, R, kind=kind, assume_sorted=True, fill_value="extrapolate"
        )
        interpZ = interp1d(
            distance, Z, kind=kind, assume_sorted=True, fill_value="extrapolate"
        )
        return lambda s: Point2D(interpR(s), interpZ(s))

    def contourSfunc(self, kind="cubic"):
        """
        Function interpolating distance as a function of index for the current state of
        this contour. When outside [startInd, endInd], set to constant so the results
        aren't affected by extrapolation errors.
        """
        interpS = interp1d(
            numpy.arange(len(self), dtype=float),
            self.distance,
            kind=kind,
            assume_sorted=True,
            fill_value="extrapolate",
        )
        thisStartInd = self.startInd
        thisEndInd = self.endInd
        if thisEndInd < 0:
            # endInd might be negative, which would mean relative to the end of the list,
            # but we need the actual index below
            thisEndInd += len(self)
        startDistance = self.distance[thisStartInd]
        endDistance = self.distance[thisEndInd]
        return lambda i: numpy.piecewise(
            i,
            [i <= 0.0, i >= thisEndInd - thisStartInd],
            [
                0.0,
                endDistance - startDistance,
                lambda i: interpS(i + thisStartInd) - startDistance,
            ],
        )

    def interpSSperp(self, vec):
        """
        Returns:
        1. a function s(s_perp) for interpolating the poloidal distance along the contour
           from the distance perpendicular to vec.
           's_perp' is modified to be a monotonically increasing function along the
           contour.
        2. the total perpendicular distance between startInd and endInd of the contour.
        """
        return self.fine_contour.interpSSperp(vec)

    def regrid(self, *args, **kwargs):
        """
        Regrid this contour, modifying the object
        """
        self.setSelfToContour(self.getRegridded(*args, **kwargs))
        return self

    def getRegridded(
        self,
        npoints,
        *,
        width=None,
        atol=None,
        sfunc=None,
        extend_lower=None,
        extend_upper=None,
    ):
        """
        Interpolate onto set of npoints points, then refine positions.
        By default points are uniformly spaced, this can be changed by passing 'sfunc'
        which replaces the uniform interval 's' with 's=sfunc(s)'.
        'extend_lower' and 'extend_upper' extend the contour past its existing ends by a
        number of points.
        Returns a new PsiContour.

        Note: '*,' in the arguments list forces the following arguments to be passed as
        keyword, not positional, arguments
        """
        if width is None:
            width = PsiContour.options.refine_width
        if atol is None:
            atol = PsiContour.options.refine_atol

        if extend_lower is not None:
            self.extend_lower = extend_lower
        if extend_upper is not None:
            self.extend_upper = extend_upper
        self.temporaryExtend(
            extend_lower=self.extend_lower,
            extend_upper=self.extend_upper,
            ds_lower=calc_distance(self[1], self[0]),
            ds_upper=calc_distance(self[-2], self[-1]),
        )

        indices = numpy.linspace(
            -self.extend_lower,
            (npoints - 1 + self.extend_upper),
            npoints + self.extend_lower + self.extend_upper,
        )
        if sfunc is not None:
            s = sfunc(indices)

            # offset fine_contour.interpFunction in case sfunc(0.)!=0.
            sbegin = sfunc(0.0)
        else:
            s = (
                (self.distance[self.endInd] - self.distance[self.startInd])
                / (npoints - 1)
                * indices
            )
            sbegin = 0.0

        # Check s does not go beyond the end of self.fine_contour
        # If self._fine_contour is reset to None later on, this extension will be lost,
        # but it should not be reset after a contour is re-gridded, because the
        # re-gridding should be the last change that is made to a PsiContour
        orig_extend_lower = self.fine_contour.extend_lower_fine
        orig_extend_upper = self.fine_contour.extend_upper_fine

        tol_lower = 0.25 * (
            self.fine_contour.distance[1] - self.fine_contour.distance[0]
        )
        while (
            s[0] < -self.fine_contour.distance[self._fine_contour.startInd] - tol_lower
        ):
            self._fine_contour.extend(extend_lower=max(orig_extend_lower, 1))

        tol_upper = 0.25 * (
            self.fine_contour.distance[-1] - self.fine_contour.distance[-2]
        )
        while (
            s[-1]
            > self.fine_contour.distance[-1]
            - self.fine_contour.distance[self.fine_contour.startInd]
            + tol_upper
        ):
            self._fine_contour.extend(extend_upper=max(orig_extend_upper, 1))

        interp_unadjusted = self.fine_contour.interpFunction()

        def interp(s):
            return interp_unadjusted(s - sbegin)

        new_contour = self.newContourFromSelf(points=[interp(x) for x in s])
        new_contour.startInd = self.extend_lower
        new_contour.endInd = len(new_contour) - 1 - self.extend_upper
        new_contour._distance = None
        # re-use the extended fine_contour for new_contour
        new_contour._fine_contour = self.fine_contour

        # new_contour was interpolated from a high-resolution contour, so should not need
        # a large width for refinement - use width/100. instead of 'width'
        new_contour.refine(width=width / 100.0, atol=atol)

        # Pass already converged fine_contour to new_contour
        new_contour._fine_contour = self.fine_contour

        return new_contour

    def checkFineContourExtend(self):
        """
        Ensure that self._fine_contour extends past the first and last points of this
        PsiContour
        """

        # check first point
        p = numpy.array([*self[0]])
        distances = numpy.sqrt(
            numpy.sum((self.fine_contour.positions - p[numpy.newaxis, :]) ** 2, axis=1)
        )
        minind = numpy.argmin(distances)
        # if minind > 0, or the distance to point 1 is less than the distance between
        # point 0 and point 1 of the fine_contour, then fine_contour extends past p so
        # does not need to be extended
        if minind == 0 and distances[1] > numpy.sqrt(
            numpy.sum(
                (self.fine_contour.positions[1, :] - self.fine_contour.positions[0, :])
                ** 2
            )
        ):

            ds = self.fine_contour.distance[1] - self.fine_contour.distance[0]
            n_extend_lower = max(int(numpy.ceil(distances[0] / ds)), 1)
        else:
            n_extend_lower = 0

        # check last point
        p = numpy.array([*self[-1]])
        distances = numpy.sqrt(
            numpy.sum((self.fine_contour.positions - p[numpy.newaxis, :]) ** 2, axis=1)
        )
        minind = numpy.argmin(distances)
        # if minind < len(distances)-1, or the distance to the last point is less than
        # the distance between the last and second-last of the fine_contour, then
        # fine_contour extends past p so does not need to be extended
        if minind == len(distances) - 1 and distances[-2] > numpy.sqrt(
            numpy.sum(
                (
                    self.fine_contour.positions[-1, :]
                    - self.fine_contour.positions[-2, :]
                )
                ** 2
            )
        ):

            ds = self.fine_contour.distance[-1] - self.fine_contour.distance[-2]
            n_extend_upper = max(int(numpy.ceil(distances[-1] / ds)), 1)
        else:
            n_extend_upper = 0

        if n_extend_lower == 0 and n_extend_upper == 0:
            return
        else:
            self.fine_contour.extend(
                extend_lower=n_extend_lower, extend_upper=n_extend_upper
            )
            # Call recursively to check extending has gone far enough
            self.checkFineContourExtend()

    def temporaryExtend(
        self, *, extend_lower=0, extend_upper=0, ds_lower=None, ds_upper=None
    ):
        """
        Add temporary guard-cell points to the beginning and/or end of a contour
        Use coarseInterp to extrapolate as using a bigger spacing gives a more stable
        extrapolation.
        """
        if extend_lower > 0:
            if ds_lower is None:
                ds = self.distance[1] - self.distance[0]
            else:
                ds = ds_lower
            for i in range(extend_lower):
                extrap = self._coarseExtrapLower(0)
                new_point = extrap(-ds)
                self.prepend(self.refinePoint(new_point, new_point - self[0]))
                if self.startInd >= 0:
                    self.startInd += 1
                if self.endInd >= 0:
                    self.endInd += 1
        if extend_upper > 0:
            if ds_upper is None:
                ds = self.distance[-1] - self.distance[-2]
            else:
                ds = ds_upper
            for i in range(extend_upper):
                extrap = self._coarseExtrapUpper(-1)
                new_point = extrap(ds)
                self.append(self.refinePoint(new_point, new_point - self[-1]))
                if self.endInd < 0:
                    self.endInd -= 1

    def plot(self, *args, plotPsi=False, **kwargs):
        from matplotlib import pyplot

        Rpoints = [p.R for p in self]
        Zpoints = [p.Z for p in self]
        if plotPsi:
            R = numpy.linspace(min(Rpoints), max(Rpoints), 100)
            Z = numpy.linspace(min(Zpoints), max(Zpoints), 100)
            pyplot.contour(R, Z, self.psi(R[numpy.newaxis, :], Z[:, numpy.newaxis]))
        pyplot.plot(Rpoints, Zpoints, *args, **kwargs)


class EquilibriumRegion(PsiContour):
    """
    Specialization of PsiContour for representing an equilibrium segment, which is a
    poloidal segment based around a contour (normally a segment of a separatrix).
    Includes members giving the connections to other regions and to list the X-points at
    the boundaries where the contour starts or ends.
    """

    def __init__(
        self, equilibrium, name, nSegments, user_options, options, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.equilibrium = equilibrium
        self.name = name
        self.nSegments = nSegments

        self.user_options = user_options

        # Set up options for this object: poloidal spacing options need setting
        self.options = options.push({})

        # Set object-specific options
        assert self.options.nx is not None, "nx must be set"
        assert self.options.ny is not None, "ny must be set"

        # Allow options to be overridden by kwargs
        self.options = self.options.push(kwargs)

        self.setupOptions(force=False)
        self.ny_noguards = self.options.ny
        self.global_xind = (
            0  # 0 since EquilibriumRegion represents the contour at the separatrix
        )

        self.xPointsAtStart = []
        self.xPointsAtEnd = []

        # Set if this segment starts on a wall, with value of vector along wall
        self.wallSurfaceAtStart = None

        # Set if this segment ends on a wall, with value of vector along wall
        self.wallSurfaceAtEnd = None

        self.connections = []
        self.psi_vals = []
        self.separatrix_radial_index = 0

        # xPointsAtStart and xPointsAtEnd should have an entry at the lower and upper
        # side of each segment, so they both have length=nSegments+1
        self.xPointsAtStart.append(None)
        self.xPointsAtEnd.append(None)
        for i in range(nSegments):
            c = {"inner": None, "outer": None, "lower": None, "upper": None}
            if i > 0:
                c["inner"] = (self.name, i - 1)
            if i < nSegments - 1:
                c["outer"] = (self.name, i + 1)
            self.connections.append(c)
            self.xPointsAtStart.append(None)
            self.xPointsAtEnd.append(None)

    def setupOptions(self, *, force):
        def setoption(key, val):
            if force:
                self.options[key] = val
            else:
                setDefault(self.options, key, val)

        # Set default values depending on options.kind
        if self.options.kind.split(".")[0] == "wall":
            setoption("sqrt_b_lower", self.user_options.target_poloidal_spacing_length)
            setoption(
                "monotonic_d_lower",
                self.user_options.nonorthogonal_target_poloidal_spacing_length,
            )
            setoption(
                "nonorthogonal_range_lower",
                self.user_options.nonorthogonal_target_poloidal_spacing_range,
            )
            setoption(
                "nonorthogonal_range_lower_inner",
                self.user_options.nonorthogonal_target_poloidal_spacing_range_inner,
            )
            setoption(
                "nonorthogonal_range_lower_outer",
                self.user_options.nonorthogonal_target_poloidal_spacing_range_outer,
            )
        elif self.options.kind.split(".")[0] == "X":
            setoption("sqrt_a_lower", self.user_options.xpoint_poloidal_spacing_length)
            setoption("sqrt_b_lower", 0.0)
            setoption(
                "monotonic_d_lower",
                self.user_options.nonorthogonal_xpoint_poloidal_spacing_length,
            )
            setoption(
                "nonorthogonal_range_lower",
                self.user_options.nonorthogonal_xpoint_poloidal_spacing_range,
            )
            setoption(
                "nonorthogonal_range_lower_inner",
                self.user_options.nonorthogonal_xpoint_poloidal_spacing_range_inner,
            )
            setoption(
                "nonorthogonal_range_lower_outer",
                self.user_options.nonorthogonal_xpoint_poloidal_spacing_range_outer,
            )
        else:
            raise ValueError(
                f"Unrecognized value before '.' in " f"kind={self.options.kind}"
            )
        if self.options.kind.split(".")[1] == "wall":
            setoption("sqrt_b_upper", self.user_options.target_poloidal_spacing_length)
            setoption(
                "monotonic_d_upper",
                self.user_options.nonorthogonal_target_poloidal_spacing_length,
            )
            setoption(
                "nonorthogonal_range_upper",
                self.user_options.nonorthogonal_target_poloidal_spacing_range,
            )
            setoption(
                "nonorthogonal_range_upper_inner",
                self.user_options.nonorthogonal_target_poloidal_spacing_range_inner,
            )
            setoption(
                "nonorthogonal_range_upper_outer",
                self.user_options.nonorthogonal_target_poloidal_spacing_range_outer,
            )
        elif self.options.kind.split(".")[1] == "X":
            setoption("sqrt_a_upper", self.user_options.xpoint_poloidal_spacing_length)
            setoption("sqrt_b_upper", 0.0)
            setoption(
                "monotonic_d_upper",
                self.user_options.nonorthogonal_xpoint_poloidal_spacing_length,
            )
            setoption(
                "nonorthogonal_range_upper",
                self.user_options.nonorthogonal_xpoint_poloidal_spacing_range,
            )
            setoption(
                "nonorthogonal_range_upper_inner",
                self.user_options.nonorthogonal_xpoint_poloidal_spacing_range_inner,
            )
            setoption(
                "nonorthogonal_range_upper_outer",
                self.user_options.nonorthogonal_xpoint_poloidal_spacing_range_outer,
            )
        else:
            raise ValueError(
                "Unrecognized value before '.' in self.options.kind="
                + str(self.options.kind)
            )

    def copy(self):
        result = EquilibriumRegion(
            self.equilibrium,
            self.name,
            self.nSegments,
            self.user_options,
            self.options,
            deepcopy(self.points),
            self.psi,
            self.psival,
        )
        result.xPointsAtStart = deepcopy(self.xPointsAtStart)
        result.xPointsAtEnd = deepcopy(self.xPointsAtEnd)
        result.wallSurfaceAtStart = deepcopy(self.wallSurfaceAtStart)
        result.wallSurfaceAtEnd = deepcopy(self.wallSurfaceAtEnd)
        result.connections = deepcopy(self.connections)
        result.psi_vals = deepcopy(self.psi_vals)
        result.separatrix_radial_index = self.separatrix_radial_index
        result.startInd = self.startInd
        result.endInd = self.endInd
        result.extend_lower = self.extend_lower
        result.extend_upper = self.extend_upper
        return result

    def newRegionFromPsiContour(self, contour):
        result = EquilibriumRegion(
            self.equilibrium,
            self.name,
            self.nSegments,
            self.user_options,
            self.options,
            contour.points,
            contour.psi,
            contour.psival,
        )
        result.xPointsAtStart = deepcopy(self.xPointsAtStart)
        result.xPointsAtEnd = deepcopy(self.xPointsAtEnd)
        result.wallSurfaceAtStart = deepcopy(self.wallSurfaceAtStart)
        result.wallSurfaceAtEnd = deepcopy(self.wallSurfaceAtEnd)
        result.connections = deepcopy(self.connections)
        result.psi_vals = deepcopy(self.psi_vals)
        result.separatrix_radial_index = self.separatrix_radial_index
        result.startInd = contour.startInd
        result.endInd = contour.endInd
        result.extend_lower = contour.extend_lower
        result.extend_upper = contour.extend_upper
        return result

    def ny(self, radialIndex):
        # Get ny for a segment of this EquilibriumRegion, including any y-boundary guard
        # cells
        result = self.ny_noguards
        if self.connections[radialIndex]["lower"] is None:
            result += self.user_options.y_boundary_guards
        if self.connections[radialIndex]["upper"] is None:
            result += self.user_options.y_boundary_guards
        return result

    def nxOutsideSeparatrix(self):
        # Note: includes point at separatrix
        return 1 + sum(2 * n for n in self.options.nx[self.separatrix_radial_index :])

    def nxInsideSeparatrix(self):
        # Note: also includes point at separatrix
        return 1 + sum(2 * n for n in self.options.nx[: self.separatrix_radial_index])

    def getRefined(self, *args, **kwargs):
        return self.newRegionFromPsiContour(super().getRefined(*args, **kwargs))

    def getRegridded(self, *, radialIndex, **kwargs):
        for wrong_argument in ["npoints", "extend_lower", "extend_upper", "sfunc"]:
            # these are valid arguments to PsiContour.getRegridded, but not to
            # EquilibriumRegion.getRegridded. EquilibriumRegion.getRegridded knows its
            # own ny and connections, so must use these
            if wrong_argument in kwargs:
                raise ValueError(
                    "'" + wrong_argument + "' should not be given as an "
                    "argument to EquilibriumRegion.getRegridded"
                )
        if self.connections[radialIndex]["lower"] is None:
            extend_lower = 2 * self.user_options.y_boundary_guards
        else:
            extend_lower = 0
        if self.connections[radialIndex]["upper"] is None:
            extend_upper = 2 * self.user_options.y_boundary_guards
        else:
            extend_upper = 0
        sfunc = self.getSfuncFixedSpacing(
            2 * self.ny_noguards + 1,
            self.distance[self.endInd] - self.distance[self.startInd],
        )
        return self.newRegionFromPsiContour(
            super().getRegridded(
                2 * self.ny_noguards + 1,
                extend_lower=extend_lower,
                extend_upper=extend_upper,
                sfunc=sfunc,
                **kwargs,
            )
        )

    def _checkMonotonic(self, sfunc_list, *, xind=None, total_distance=0.0, prefix=""):
        # Check new_sfunc is monotonically increasing
        indices = numpy.arange(
            -self.extend_lower,
            2 * self.ny_noguards + self.extend_upper + 1,
            dtype=float,
        )
        scheck = sfunc_list[0][0](indices)
        if numpy.any(scheck[1:] < scheck[:-1]):
            from matplotlib import pyplot

            print("at global xind", xind)
            pyplot.figure()
            for sfunc, label in sfunc_list:
                if sfunc is not None:
                    pyplot.plot(indices, sfunc(indices), label=label)
            pyplot.axhline(0.0)
            pyplot.axhline(total_distance)
            pyplot.legend()
            pyplot.show()
            decreasing = numpy.where(scheck[1:] < scheck[:-1])[0] + 1
            raise ValueError(
                f"In region {self.name} combined spacing function is decreasing at "
                f"indices {decreasing} on contour of length {len(self)}. It may help to "
                f"increase/decrease {prefix}target_poloidal_spacing_length or "
                f"{prefix}xpoint_poloidal_spacing_length."
            )

    def getSfuncFixedSpacing(self, npoints, distance, *, method=None):
        if method is None:
            if self.user_options.orthogonal:
                method = self.user_options.poloidal_spacing_method
            else:
                method = "nonorthogonal"

        if method == "sqrt":
            if self.user_options.poloidalfunction_diagnose:
                print("in sqrt method:")
                print("N_norm =", self.options.N_norm)
                print("a_lower =", self.options.sqrt_a_lower)
                print("b_lower =", self.options.sqrt_b_lower)
                print("a_upper =", self.options.sqrt_a_upper)
                print("b_upper =", self.options.sqrt_b_upper)
            sfunc = self.getSqrtPoloidalDistanceFunc(
                distance,
                npoints - 1,
                self.options.N_norm,
                b_lower=self.options.sqrt_b_lower,
                a_lower=self.options.sqrt_a_lower,
                b_upper=self.options.sqrt_b_upper,
                a_upper=self.options.sqrt_a_upper,
            )
            self._checkMonotonic([(sfunc, "sqrt")], total_distance=distance)
        elif method == "monotonic":
            sfunc = self.getMonotonicPoloidalDistanceFunc(
                distance,
                npoints - 1,
                self.options.N_norm,
                d_lower=self.options.monotonic_d_lower,
                d_upper=self.options.monotonic_d_upper,
            )
            self._checkMonotonic([(sfunc, "sqrt")], total_distance=distance)
        elif method == "nonorthogonal":
            nonorth_method = self.user_options.nonorthogonal_spacing_method
            if nonorth_method == "poloidal_orthogonal_combined":
                return self.combineSfuncs(self, None)
            elif nonorth_method == "perp_orthogonal_combined":
                if self.wallSurfaceAtStart is not None:
                    # surface is a wall
                    lower_surface = self.wallSurfaceAtStart
                else:
                    # Use fixed poloidal spacing when gridding the separatrix contour so
                    # that the grid spacing is the same in different regions which share
                    # a separatrix segment but have different perpendicular vectors at
                    # the X-point
                    lower_surface = None

                if self.wallSurfaceAtEnd is not None:
                    # surface is a wall
                    upper_surface = self.wallSurfaceAtEnd
                else:
                    # Use fixed poloidal spacing when gridding the separatrix contour so
                    # that the grid spacing is the same in different regions which share
                    # a separatrix segment but have different perpendicular vectors at
                    # the X-point
                    upper_surface = None

                sfunc = self.combineSfuncs(self, None, lower_surface, upper_surface)
            elif nonorth_method == "combined":
                # Use fixed poloidal spacing when gridding the separatrix contour so that
                # the grid spacing is the same in different regions which share a
                # separatrix segment but have different perpendicular vectors at the
                # X-point
                return self.combineSfuncs(self, None)
            elif nonorth_method == "orthogonal":
                orth_method = self.user_options.poloidal_spacing_method
                sfunc = self.getSfuncFixedSpacing(npoints, distance, method=orth_method)
            else:
                sfunc = self.getSfuncFixedSpacing(
                    npoints, distance, method=nonorth_method
                )
        else:
            raise ValueError(
                "Unrecognized option "
                + str(self.user_options.poloidal_spacing_method)
                + " for poloidal spacing method"
            )

        if self.user_options.poloidalfunction_diagnose:
            from matplotlib import pyplot

            indices = numpy.linspace(0.0, npoints - 1, 1000)
            pyplot.plot(indices, sfunc(indices))
            pyplot.axhline(0.0, color="r")
            pyplot.axhline(distance, color="r")
            pyplot.xlabel("index")
            pyplot.ylabel("s")
            pyplot.title(self.name + " " + method)
            pyplot.show()

        return sfunc

    def combineSfuncs(self, contour, sfunc_orthogonal, vec_lower=None, vec_upper=None):
        # this sfunc gives:
        # * - if vec_lower is None: fixed poloidal spacing at the beginning of the
        #     contour
        #   - otherwise fixed spacing perpendicular to vec_lower at the beginning of the
        #     contour
        # * - if vec_upper is None: fixed poloidal spacing at the end of the contour
        #   - otherwise fixed spacing perpendicular to vec_lower at the end of the
        #     contour
        # * Tends to orthogonal spacing far from the ends, unless sfunc_orthogonal is
        #   None, in which case it sets points so that if combineSfuncs is called again
        #   on the same contour, but with sfunc_orthogonal=contour.contourSfunc() then
        #   the same spacing is given
        if vec_lower is None:
            sfunc_fixed_lower = self.getSfuncFixedSpacing(
                2 * self.ny_noguards + 1, contour.totalDistance(), method="monotonic"
            )
        else:
            sfunc_fixed_lower, sperp_func_lower = self.getSfuncFixedPerpSpacing(
                2 * self.ny_noguards + 1, contour, vec_lower, True
            )

        if vec_upper is None:
            sfunc_fixed_upper = self.getSfuncFixedSpacing(
                2 * self.ny_noguards + 1, contour.totalDistance(), method="monotonic"
            )
        else:
            sfunc_fixed_upper, sperp_func_upper = self.getSfuncFixedPerpSpacing(
                2 * self.ny_noguards + 1, contour, vec_upper, False
            )

        if self.options.nonorthogonal_range_lower is not None:
            range_lower = self.options.nonorthogonal_range_lower
            range_lower_inner = self.options.nonorthogonal_range_lower_inner
            range_lower_outer = self.options.nonorthogonal_range_lower_outer
        else:
            range_lower = self.options.monotonic_d_lower
            range_lower_inner = self.options.monotonic_d_lower
            range_lower_outer = self.options.monotonic_d_lower

        if self.options.nonorthogonal_range_upper is not None:
            range_upper = self.options.nonorthogonal_range_upper
            range_upper_inner = self.options.nonorthogonal_range_upper_inner
            range_upper_outer = self.options.nonorthogonal_range_upper_outer
        else:
            range_upper = self.options.monotonic_d_upper
            range_upper_inner = self.options.monotonic_d_upper
            range_upper_outer = self.options.monotonic_d_upper

        N_norm = self.options.N_norm

        index_length = 2.0 * self.ny_noguards

        # Set up radial variation of weights
        if range_lower is not None:
            # this_range_lower is range_lower at separatrix, range_lower_outer at outer
            # radial boundary, range_lower_inner at inner radial boundary and has zero
            # radial derivative at the separatrix
            ix = float(contour.global_xind)
            if ix >= 0:
                xweight = (
                    ix / (self.nxOutsideSeparatrix() - 1.0)
                ) ** self.user_options.nonorthogonal_radial_range_power
                this_range_lower = (
                    1.0 - xweight
                ) * range_lower + xweight * range_lower_outer
            else:
                xweight = (
                    -ix / (self.nxInsideSeparatrix() - 1.0)
                ) ** self.user_options.nonorthogonal_radial_range_power
                this_range_lower = (
                    1.0 - xweight
                ) * range_lower + xweight * range_lower_inner
        if range_upper is not None:
            # this_range_upper is range_upper at separatrix, range_upper_outer at outer
            # radial boundary, range_upper_inner at inner radial boundary and has zero
            # radial derivative at the separatrix
            ix = float(contour.global_xind)
            if ix >= 0:
                xweight = (
                    ix / (self.nxOutsideSeparatrix() - 1.0)
                ) ** self.user_options.nonorthogonal_radial_range_power
                this_range_upper = (
                    1.0 - xweight
                ) * range_upper + xweight * range_upper_outer
            else:
                xweight = (
                    -ix / (self.nxInsideSeparatrix() - 1.0)
                ) ** self.user_options.nonorthogonal_radial_range_power
                this_range_upper = (
                    1.0 - xweight
                ) * range_upper + xweight * range_upper_inner

        if range_lower is not None and range_upper is not None:

            def new_sfunc(i):
                sfixed_lower = sfunc_fixed_lower(i)

                sfixed_upper = sfunc_fixed_upper(i)

                if sfunc_orthogonal is None:
                    sorth = None
                else:
                    sorth = sfunc_orthogonal(i)

                # define weight_lower so it is 1. at the lower boundary and 0. at the
                # upper boundary and the gradient is zero at both boundaries
                weight_lower = numpy.piecewise(
                    i,
                    [i < 0.0, i > index_length],
                    [
                        1.0,
                        0.0,
                        lambda i: numpy.exp(-((i / N_norm / this_range_lower) ** 2)),
                    ],
                )

                # define weight_upper so it is 1. at the upper boundary and 0. at the
                # lower boundary and the gradient is zero at both boundaries
                weight_upper = numpy.piecewise(
                    i,
                    [i < 0.0, i > index_length],
                    [
                        0.0,
                        1.0,
                        lambda i: numpy.exp(
                            -(((index_length - i) / N_norm / this_range_upper) ** 2)
                        ),
                    ],
                )

                # make sure weight_lower + weight_upper <= 1
                weight = weight_lower + weight_upper
                weight_over_slice = weight[weight > 1.0]
                weight_lower[weight > 1.0] /= weight_over_slice
                weight_upper[weight > 1.0] /= weight_over_slice

                if sorth is None:
                    # Fix spacing so that if we call combineSfuncs again for this contour
                    # with sfunc_orthogonal from self.contourSfunc() then we get the same
                    # spacing again. This is used to make the contours along the
                    # separatrix keep the same values when pushing the other contours
                    # towards orthogonal positions
                    # s = weight_lower*sfixed_lower
                    #     + weight_upper*sfixed_upper
                    #     + (1. - weight_lower - weight_upper)*s
                    sorth = (
                        weight_lower * sfixed_lower + weight_upper * sfixed_upper
                    ) / (weight_lower + weight_upper)

                return (
                    weight_lower * sfixed_lower
                    + weight_upper * sfixed_upper
                    + (1.0 - weight_lower - weight_upper) * sorth
                )

        elif range_lower is not None:

            def new_sfunc(i):
                sfixed_lower = sfunc_fixed_lower(i)

                if sfunc_orthogonal is None:
                    sorth = None
                else:
                    sorth = sfunc_orthogonal(i)

                # define weight_lower so it is 1. at the lower boundary and the gradient
                # is zero at the lower boundary.
                weight_lower = numpy.piecewise(
                    i,
                    [i < 0.0, i > index_length],
                    [
                        1.0,
                        0.0,
                        lambda i: numpy.exp(-((i / N_norm / this_range_lower) ** 2)),
                    ],
                )

                if sorth is None:
                    # Fix spacing so that if we call combineSfuncs again for this contour
                    # with sfunc_orthogonal from self.contourSfunc() then we get the same
                    # spacing again. This is used to make the contours along the
                    # separatrix keep the same values when pushing the other contours
                    # towards orthogonal positions
                    # s = weight_lower*sfixed_lower + (1. - weight_lower)*s
                    sorth = sfixed_lower

                return (weight_lower) * sfixed_lower + (1.0 - weight_lower) * sorth

        elif range_upper is not None:

            def new_sfunc(i):
                sfixed_upper = sfunc_fixed_upper(i)

                if sfunc_orthogonal is None:
                    sorth = None
                else:
                    sorth = sfunc_orthogonal(i)

                # define weight_upper so it is 1. at the upper boundary and the gradient
                # is zero at the upper boundary.
                weight_upper = numpy.piecewise(
                    i,
                    [i < 0.0, i > index_length],
                    [
                        0.0,
                        1.0,
                        lambda i: numpy.exp(
                            -(((index_length - i) / N_norm / this_range_upper) ** 2)
                        ),
                    ],
                )

                if sorth is None:
                    # Fix spacing so that if we call combineSfuncs again for this contour
                    # with sfunc_orthogonal from self.contourSfunc() then we get the same
                    # spacing again. This is used to make the contours along the
                    # separatrix keep the same values when pushing the other contours
                    # towards orthogonal positions
                    # s = weight_upper*sfixed_upper + (1. - weight_upper)*s
                    sorth = sfixed_upper

                return (weight_upper) * sfixed_upper + (1.0 - weight_upper) * sorth

        else:
            assert sfunc_orthogonal is not None, (
                "Without range_lower or range_upper, cannot use with "
                "sfunc_orthogonal=None"
            )

            def new_sfunc(i):
                return sfunc_orthogonal(i)

        try:
            self._checkMonotonic(
                [
                    (new_sfunc, "combined"),
                    (sfunc_orthogonal, "orthogonal"),
                    (sfunc_fixed_lower, "fixed perp lower"),
                    (sfunc_fixed_upper, "fixed perp upper"),
                ],
                xind=contour.global_xind,
                total_distance=contour.totalDistance(),
                prefix="nonorthogonal_",
            )
        except ValueError:
            print(
                "check lower ranges",
                range_lower_inner,
                range_lower,
                range_lower_outer,
                this_range_lower,
            )
            print(
                "check upper ranges",
                range_upper_inner,
                range_upper,
                range_upper_outer,
                this_range_upper,
            )
            raise

        return new_sfunc

    def getSfuncFixedPerpSpacing(self, N, contour, surface_direction, lower):
        """
        Return a function s(i) giving poloidal distance as a function of index-number.
        Construct so that ds_perp/diN = d_lower at the lower end or ds_perp/diN = d_upper
        at the upper end, where s_perp is the distance normal to the vector
        'surface_direction'.
        """
        N_norm = self.options.N_norm

        if self.options.perp_d_lower is not None:
            d_lower = self.options.perp_d_lower
        else:
            d_lower = self.options.monotonic_d_lower

        if self.options.perp_d_upper is not None:
            d_upper = self.options.perp_d_upper
        else:
            d_upper = self.options.monotonic_d_upper

        s_of_sperp, s_perp_total = contour.interpSSperp(surface_direction)
        sperp_func = self.getMonotonicPoloidalDistanceFunc(
            s_perp_total, N - 1, N_norm, d_lower=d_lower, d_upper=d_upper
        )
        return lambda i: s_of_sperp(sperp_func(i)), sperp_func

    def getMonotonicPoloidalDistanceFunc(self, length, N, N_norm, *, d_lower, d_upper):
        """
        Return a function s(i) giving poloidal distance as a function of index-number.
        Construct s(i)=sN(iN) as a function of the normalized iN = i/N_norm so that it
        has the same form when resolution is changed. The total Ny in the grid might be a
        good choice for N_norm.
        sN(0) = 0
        sN(N/N_norm) = L
        dsN/diN(0) = d_lower at iN=0
        dsN/diN(N/N_norm) = d_upper at iN=N_norm
        sN(iN) = d_lower*iN for iN < 0
        sN(iN) = L + d_upper*(iN - N/N_norm) for iN > N/N_norm

        Define sprime=dsN/diN.
        Want sprime to be a positive definite function in the interval {0, N/N_norm},
        with sprime(0) = d_lower and sprime(N/N_norm) = d_upper, and
        \\int(diN sprime) = L

        If we chose a linear function
          sprime = a*iN + b
        then we would have
          sprime(0) = d_lower = b
          sprime(N/N_norm) = d_upper = a*N/N_norm + b
                         a = (d_upper - b)*N_norm/N
                           = (d_upper - d_lower)*N_norm/N,
        and so
          \\int(diN sprime) = 1/2*a*(N/N_norm)^2 + b*N/N_norm
                           = 1/2*(d_upper - d_lower)*N/N_norm + d_lower*N/N_norm
                           = 1/2*(d_upper + d_lower)*N/N_norm.
        We need
          \\int(diN sprime) = L
        so if
          L < 1/2*(d_upper + d_lower)*N/N_norm
        sprime has to be a concave function (curves below a straight line) and otherwise
        sprime has to be a convex function (bulges above a straight line).
        In the second case sprime is always going to be positive, and we can use a
        quadratic function for sprime (so sN will be a cubic).
        In the first case it is harder to guarantee that sprime is always positive. Here
        is one attempt:
        # Define a function, l(iN), proportional to something like 1/iN that goes through
        # d_lower at 0 and 0 at N/N_norm
            l(iN) = l1/(iN + l2) - l3 with l1, l2, l3 > 0
            l(0) = d_lower
                 = l1/l2 - l3
            l(N/N_norm) = 0
                        = l1/(N/N_norm + l2) - l3
          If we parameterise the family of these functions by l1, we can solve for l2, l3
          as
            d_lower = l1/l2 - l1/(N/N_norm + l2)
            d_lower*N/N_norm*l2 + d_lower*l2^2 = l1*N/N_norm + l1*l2 - l1*l2
                                               = l1*N/N_norm
            l2 = (-d_lower*N/N_norm
                  + sqrt(d_lower^2*(N/N_norm)^2
                  + 4*d_lower*l1*N/N_norm)
                 ) / (2*d_lower)
          taking the positive sign so that l2 > 0
            l3 = l1/l2 - d_lower
        # Define another function, r(iN), proportional to something like -1/iN that goes
          through 0 at 0 and d_upper at N/N_norm
            r(iN) = r1/(r2 + N/N_norm - iN) - r3 where r1, r2, r3 > 0
            r(0) = 0 = r1/(r2 + N/N_norm) - r3
            r(N/N_norm) = d_upper = r1/r2 - r3
          (these are identical to equations above for l1, l2, l3 but with l->r and
          d_lower->d_upper)
            r2 = (-d_upper*N/N_norm
                  + sqrt(d_upper^2*(N/N_norm)^2
                  + 4*d_upper*r1*N/N_norm)
                 ) / (2*d_upper)
            r3 = r1/r2 - d_upper
        # Let
            sprime(iN) = l(iN) + r(iN).
          We have two free parameters, l1 and r1, but only one constraint that the
          integral should be L, so arbitrarily choose l1=r1 to reduce to one free
          parameter.
        # Impose the constraint.
            int(diN l) = int(diN l1/(iN + l2) - l3)
                       = [l1*ln(iN + l2) - l3*iN]_{0}^{N/N_norm}
                       = l1*ln(N/(N_norm*l2) + 1) - l3*N/N_norm
            int(diN r) = int(diN r1/(r2 + N/N_norm - iN) - r3)
                       = [-r1*ln(r2 + N/N_norm - iN) - r3*iN]_{0}^{N/N_norm}
                       = r1*ln(1 + N/(N_norm*r2) - r3*N/N_norm)
            L = int(diN l) + int(diN r)
              = l1*ln(N/(N_norm*l2) + 1) - l3*N/N_norm
                + r1*ln(N/(N_norm*r2) + 1) - r3*N/N_norm
              = l1*ln(N/(N_norm*l2) + 1) - l3*N/N_norm
                + l1*ln(N/(N_norm*r2) + 1) - r3*N/N_norm.
          This is a horrible equation with logs in and l1 both inside and outside logs,
          probably can't solve by hand, but should have a unique solution and be a
          monotonic function of l1, so solve numerically.

        In the first case we have
          s(iN) = a*iN^2 + b*iN + c
          s(0) = d_lower = c
          s(N/N_norm) = d_upper = a*(N/N_norm)^2 + b*N/N_norm + d_lower
                    b = (d_upper - d_lower)*N_norm/N - a*N/N_norm
        The constraint on the integral gives
          L = int(diN s) = int(diN (a*iN^2 + b*iN + c))
            = 1/3*a*(N/N_norm)^3 + 1/2*b*(N/N_norm)^2 + c*N/N_norm
            = 1/3*a*(N/N_norm)^3 + 1/2*(d_upper - d_lower)*N/N_norm
              - 1/2*a*(N/N_norm)^3 + d_lower*N/N_norm
          1/6*(N/N_norm)^3*a = 1/2(d_upper + d_lower)*N/N_norm - L
          a = 3*(d_upper + d_lower)*(N_norm/N)^2 - 6*L*(N_norm/N)^3
        """
        # Add a small tolerance (1.e-8*length) here because when the concave case gets
        # very close to linear l1 will get very large so the root-finding might possibly
        # fail, but very close to the linear case, the quadratic expression in the convex
        # case should be a good one
        if length < 0.5 * (d_upper + d_lower) * N / N_norm - 1.0e-8 * length:
            # concave case

            # Make coefficients as functions of l1
            def l2(l1):
                return (
                    -d_lower * N / N_norm
                    + numpy.sqrt(
                        (d_lower * N / N_norm) ** 2 + 4.0 * d_lower * l1 * N / N_norm
                    )
                ) / (2.0 * d_lower)

            def l3(l1):
                return l1 / l2(l1) - d_lower

            def r2(l1):
                return (
                    -d_upper * N / N_norm
                    + numpy.sqrt(
                        (d_upper * N / N_norm) ** 2 + 4.0 * d_upper * l1 * N / N_norm
                    )
                ) / (2.0 * d_upper)

            def r3(l1):
                return l1 / r2(l1) - d_upper

            # Make constraint function to find value of l1 where the integral equals L
            def constraint(l1):
                return (
                    l1 * numpy.log(N / (N_norm * l2(l1)) + 1.0)
                    - l3(l1) * N / N_norm
                    + l1 * numpy.log(N / (N_norm * r2(l1)) + 1.0)
                    - r3(l1) * N / N_norm
                    - length
                )

            l1 = brentq(constraint, 1.0e-15, 1.0e10, xtol=1.0e-15, rtol=1.0e-10)
            l3 = l3(l1)
            l2 = l2(l1)
            r3 = r3(l1)
            r2 = r2(l1)

            # coefficients should all be positive
            assert l1 > 0.0
            assert l2 > 0.0
            assert l3 > 0.0
            assert r2 > 0.0
            assert r3 > 0.0

            # sN(iN) = int(diN sprime)
            #        = int(diN l1/(iN + l2) - l3 + l1/(r2 + N/N_norm - iN) - r3
            #        = l1*ln(iN + l2) - l1*ln(l2) - l3*iN - l1*ln(r2 + N/N_norm - iN)
            #          + l1*ln(r2 + N/N_norm) - r3*iN
            #        = l1*ln(iN/l2 + 1.) - l3*iN - l1*ln(1. - iN/(r2 + N/N_norm)) - r3*iN
            return lambda i: numpy.piecewise(
                i,
                [i < 0.0, i > N],
                [
                    lambda i: d_lower * i / N_norm,
                    lambda i: length + d_upper * (i - N) / N_norm,
                    lambda i: (
                        l1 * numpy.log(i / N_norm / l2 + 1.0)
                        - l3 * i / N_norm
                        - l1 * numpy.log(1.0 - i / (N_norm * (r2 + N / N_norm)))
                        - r3 * i / N_norm
                    ),
                ],
            )
        else:
            # convex case
            a = (
                3.0 * (d_upper + d_lower) * (N_norm / N) ** 2
                - 6.0 * length * (N_norm / N) ** 3
            )
            b = (d_upper - d_lower) * N_norm / N - a * N / N_norm
            c = d_lower

            # sN(iN) = int(diN sprime)
            #        = 1/3*a*iN^3 + 1/2*b*iN^2 + c*iN
            return lambda i: numpy.piecewise(
                i,
                [i < 0.0, i > N],
                [
                    lambda i: d_lower * i / N_norm,
                    lambda i: length + d_upper * (i - N) / N_norm,
                    lambda i: 1.0 / 3.0 * a * (i / N_norm) ** 3
                    + 0.5 * b * (i / N_norm) ** 2
                    + c * i / N_norm,
                ],
            )

    def getSqrtPoloidalDistanceFunc(
        self,
        length,
        N,
        N_norm,
        *,
        b_lower=None,
        a_lower=None,
        b_upper=None,
        a_upper=None,
    ):
        """
        Return a function s(i) giving poloidal distance as a function of index-number.
        Construct s(i)=sN(iN) as a function of the normalized iN = i/N_norm so that it
        has the same form when resolution is changed. The total Ny in the grid might be a
        good choice for N_norm.
        sN(0) = 0
        sN(N/N_norm) = L
        ds/diN(0) ~ a_lower/sqrt(iN)+b_lower at iN=0 (if a_lower not None, else no
                                                           sqrt(iN) term)
        ds/diN(N/N_norm) ~ a_upper/sqrt(N/N_norm-iN)+b_upper at iN=N_norm (if a_upper is
                                              not None, else no sqrt(N/N_norm - iN) term)

        By default a_lower=b_lower and a_upper=b_upper, unless both are
        specified explicitly
        """
        if b_lower is None and b_upper is None:
            assert a_lower is None, "cannot set a_lower unless b_lower is set"
            assert a_upper is None, "cannot set a_upper unless b_upper is set"
            # always monotonic
            return lambda i: i * length / N
        elif b_lower is None:
            assert a_lower is None, "cannot set a_lower unless b_lower is set"
            if a_upper is None:
                a_upper = 0.0
            # s(iN) = -b*sqrt(N/N_norm-iN) + c + d*iN + e*(iN)^2
            # s(0) = 0 = -b*sqrt(N/N_norm) + c
            # ds/diN(N/N_norm) = b/(2*sqrt(N/N_norm-iN))+d+2*e*N/N_norm
            #                  ~ a_upper/sqrt(N/N_norm-iN)+b_upper
            # b = 2*a_upper
            # d + 2*e*N/N_norm = b_upper
            # d = b_upper - 2*e*N/N_norm
            # s(N/N_norm) = L = c + d*N/N_norm + e*(N/N_norm)^2
            # L = c + b_upper*N/N_norm - 2*e*(N/N_norm)^2 + e*(N/N_norm)^2
            # e = (c + b_upper*N/N_norm - L) / (N/N_norm)^2
            b = 2.0 * a_upper
            c = b * numpy.sqrt(N / N_norm)
            e = (c + b_upper * N / N_norm - length) / (N / N_norm) ** 2
            d = b_upper - 2 * e * N / N_norm

            # check function is monotonic: gradients at beginning and end should both be
            # positive.
            # lower boundary:
            assert (
                b / (2.0 * numpy.sqrt(N / N_norm)) + d > 0.0
            ), "gradient at start should be positive"
            # upper boundary:
            assert b >= 0.0, "sqrt part of function should be positive at end"
            assert (
                d + 2.0 * e * N / N_norm >= 0.0
            ), "gradient of polynomial part should be positive at end"

            return (
                lambda i: -b * numpy.sqrt((N - i) / N_norm)
                + c
                + d * i / N_norm
                + e * (i / N_norm) ** 2
            )
        elif b_upper is None:
            if a_lower is None:
                a_lower = 0.0
            assert a_upper is None
            # s(iN) = a*sqrt(iN) + c + d*iN + e*iN^2
            # s(0) = 0 = c
            # ds/di(0) = a/(2*sqrt(iN))+d ~ a_lower/sqrt(iN)+b_lower
            # a = 2*a_lower
            # d = b_lower
            # s(N/N_norm) = L = a*sqrt(N/N_norm) + c + d*N/N_norm + e*(N/N_norm)^2
            a = 2.0 * a_lower
            d = b_lower
            e = (length - a * numpy.sqrt(N / N_norm) - d * N / N_norm) / (
                N / N_norm
            ) ** 2

            # check function is monotonic: gradients at beginning and end should both be
            # positive.
            # lower boundary:
            assert a >= 0.0, "sqrt part of function should be positive at start"
            assert d >= 0.0, "gradient of polynomial part should be positive at start"
            # upper boundary:
            assert (
                a / (2.0 * numpy.sqrt(N / N_norm)) + d + 2.0 * e * N / N_norm > 0.0
            ), "gradient at end should be positive"

            return (
                lambda i: a * numpy.sqrt(i / N_norm)
                + d * i / N_norm
                + e * (i / N_norm) ** 2
            )
        else:
            if a_lower is None:
                a_lower = 0.0
            if a_upper is None:
                a_upper = 0.0
            # s(iN) = a*sqrt(iN) - b*sqrt(N/N_norm-iN) + c + d*iN + e*iN^2 + f*iN^3
            # s(0) = 0 = -b*sqrt(N/N_norm) + c
            # c = b*sqrt(N/N_norm)
            # ds/diN(0) = a/(2*sqrt(iN))+b/(2*sqrt(N/N_norm))+d
            #           ~ a_lower/sqrt(iN)+b_lower
            # a = 2*a_lower
            # b/(2*sqrt(N/N_norm)) + d = b_lower
            # d = b_lower - b/(2*sqrt(N/N_norm)
            # ds/di(N) = b/(2*sqrt(N/N_norm-iN)) + a/(2*sqrt(N))
            #            + d + 2*e*N/N_norm + 3*f*(N/N_norm)^2
            #          ~ a_upper/sqrt(N/N_norm-i)+b_upper
            # b = 2*a_upper
            # a/(2*sqrt(N/N_norm) + d + 2*e*N/N_norm + 3*f*(N/N_norm)^2 = b_upper
            # e = (b_upper - a/(2*sqrt(N/N_norm)) - d)/(2*N/N_norm) - 3/2*f*N/N_norm
            # s(N/N_norm) = L = a*sqrt(N/N_norm) + c + d*N/N_norm
            #                   + e*(N/N_norm)^2 + f*(N/N_norm)^3
            # L = a*sqrt(N/N_norm) + c + d*N/N_norm
            #     + (b_upper - a/(2*sqrt(N/N_norm)) - d)*N/(2*N_norm)
            #     - 3/2*f*(N/N_norm)^3 + f*(N/N_norm)^3
            # f = 2*(a*sqrt(N/N_norm) + c + d*N/(2*N_norm) + b_upper*N/(2*N_norm)
            #     - a*sqrt(N/N_norm)/4 - L)*N_norm^3/N^3
            a = 2.0 * a_lower
            b = 2.0 * a_upper
            c = b * numpy.sqrt(N / N_norm)
            d = b_lower - b / 2.0 / numpy.sqrt(N / N_norm)
            f = (
                2.0
                * (
                    a * numpy.sqrt(N / N_norm)
                    + c
                    + d * N / N_norm / 2.0
                    + b_upper * N / N_norm / 2.0
                    - a * numpy.sqrt(N / N_norm) / 4.0
                    - length
                )
                * N_norm ** 3
                / N ** 3
            )
            e = (
                b_upper - a / 2.0 / numpy.sqrt(N / N_norm) - d
            ) * N_norm / 2.0 / N - 1.5 * f * N / N_norm

            # check function is monotonic: gradients at beginning and end should both be
            # positive. Only check the boundaries here, should really add a check that
            # gradient does not reverse in the middle somewhere...
            # lower boundary:
            assert a >= 0.0, "sqrt part of function should be positive at start"
            if a_lower == 0.0:
                # Gradient must be strictly positive as there is no positive a_lower
                # piece
                assert (
                    b / (2.0 * numpy.sqrt(N / N_norm)) + d > 0.0
                ), "gradient of non-singular part should be positive at start"
            else:
                # Might be 0., so allow tolerance for small negative values due to
                # rounding errors
                assert (
                    b / (2.0 * numpy.sqrt(N / N_norm)) + d
                    > -self.user_options.sfunc_checktol
                ), "gradient of non-singular part should be positive at start"
            # upper boundary:
            assert b >= 0.0, "sqrt part of function should be positive at end"
            if a_upper == 0.0:
                # Gradient must be strictly positive as there is no positive a_upper
                # piece
                assert (
                    a / (2.0 * numpy.sqrt(N / N_norm))
                    + d
                    + 2.0 * e * N / N_norm
                    + 3.0 * f * (N / N_norm) ** 2
                    > 0.0
                ), "gradient of non-singular part should be positive at end"
            else:
                # Might be 0., so allow tolerance for small negative values due to
                # rounding errors
                assert (
                    a / (2.0 * numpy.sqrt(N / N_norm))
                    + d
                    + 2.0 * e * N / N_norm
                    + 3.0 * f * (N / N_norm) ** 2
                    > -self.user_options.sfunc_checktol
                ), "gradient of non-singular part should be positive at end"

            return (
                lambda i: a * numpy.sqrt(i / N_norm)
                - b * numpy.sqrt((N - i) / N_norm)
                + c
                + d * i / N_norm
                + e * (i / N_norm) ** 2
                + f * (i / N_norm) ** 3
            )


class Equilibrium:
    """
    Base class to provide an interface to an interpolating function for the flux function
    psi that defines the magnetic equilibrium, along with some useful methods.

    psi is the magnetic flux function.

    f_R and f_Z are the components of a vector Grad(psi)/|Grad(psi)|**2. This vector
    points along a path perpendicular to psi-contours, and its value is ds/dpsi where s
    is the coordinate along the path, so we can follow the path by integrating this
    vector:
    R(psi) = \\int_0^\\psi f_R
    and
    Z(psi) = \\int_0^\\psi f_Z

    Derived classes must provide:
      - self.psi: function which takes two arguments, {R,Z}, and returns the value of psi
        at that position.
      - self.f_R: function which takes two arguments, {R,Z}, and returns the R
        component of the vector Grad(psi)/|Grad(psi)|**2.
      - self.f_Z: function which takes two arguments, {R,Z}, and returns the Z
        component of the vector Grad(psi)/|Grad(psi)|**2.
      - self.Bp_R: function which takes two arguments, {R,Z}, and returns the R
        component of the poloidal magnetic field.
      - self.Bp_Z: function which takes two arguments, {R,Z}, and returns the Z
        component of the poloidal magnetic field.
      - self.x_points: list of Point2D objects giving the position of the X-points
        ordered from primary X-point (nearest the core) outward
      - self.psi_sep: values of psi on the separatrices ordered the same as self.x_points
      - self.fpol: poloidal current function, takes one argument, psi, and returns fpol
        (function such that B_toroidal = fpol/R)
      - self.fpolprime: psi-derivative of fpol
      - self.Rmin, self.Rmax, self.Zmin, self.Zmax: positions of the corners of a
        bounding box for the gridding
      - self.regions: OrderedDict of EquilibriumRegion objects that specify this
        equilibrium
      - self.wall: list of Point2D giving vertices of polygon representing the wall, in
        anti-clockwise order; assumed to be closed so last element and first are taken to
        be connected
    """

    def __init__(self, **kwargs):
        """
        Does some generic setup common to all Equilibrium derived classes.
        Note: should be called by derived class __init__() constructor after the
        user_options have been initialized.
        """

        # Set up internal options
        # '.push(kwargs)' here lets the kwargs override any values (including for
        # 'internal' options that should not need to be set by the user) set as defaults
        # from HypnotoadOptions
        self.options = HypnotoadInternalOptions.push(kwargs)

        # Set some global parameters for PsiContours and FineContours
        # Convert self.user_options to a dict so we can use it to set the values in
        # FineContour.options using 'push'
        PsiContour.options = PsiContour.options.push(dict(self.user_options))
        FineContour.options = FineContour.options.push(dict(self.user_options))

        # Set some default options
        Equilibrium.updateOptions(self)

    def updateOptions(self):
        """
        Set default values from user_options
        """
        setDefault(
            self.user_options,
            "nonorthogonal_xpoint_poloidal_spacing_range_inner",
            self.user_options.nonorthogonal_xpoint_poloidal_spacing_range,
        )
        setDefault(
            self.user_options,
            "nonorthogonal_xpoint_poloidal_spacing_range_outer",
            self.user_options.nonorthogonal_xpoint_poloidal_spacing_range,
        )
        setDefault(
            self.user_options,
            "nonorthogonal_target_poloidal_spacing_range_inner",
            self.user_options.nonorthogonal_target_poloidal_spacing_range,
        )
        setDefault(
            self.user_options,
            "nonorthogonal_target_poloidal_spacing_range_outer",
            self.user_options.nonorthogonal_target_poloidal_spacing_range,
        )

        if hasattr(self, "regions"):
            for region in self.regions.values():
                region.setupOptions(force=False)

    def makeConnection(self, lowerRegion, lowerSegment, upperRegion, upperSegment):
        """
        Make a connection between the upper edge of a certain segment of lowerRegion and
        the lower edge of a certain segment of upperRegion.
        """
        # Needs to be OrderedDict so that Mesh can iterate through it in consistent order
        assert type(self.regions) == OrderedDict, "self.regions should be OrderedDict"

        lRegion = self.regions[lowerRegion]
        uRegion = self.regions[upperRegion]

        assert (
            lRegion.connections[lowerSegment]["upper"] is None
        ), "lRegion.connections['upper'] should not have been set already"
        assert (
            uRegion.connections[upperSegment]["lower"] is None
        ), "uRegion.connections['lower'] should not have been set already"

        # Check nx of both segments is the same - otherwise the connection must be
        # between some wrong regions
        assert (
            lRegion.options.nx[lowerSegment] == uRegion.options.nx[upperSegment]
        ), "nx should match across connection"

        lRegion.connections[lowerSegment]["upper"] = (upperRegion, upperSegment)
        uRegion.connections[upperSegment]["lower"] = (lowerRegion, lowerSegment)

    def magneticFunctionsFromGrid(self, R, Z, psiRZ):
        from ..utils.dct_interpolation import DCT_2D

        self._dct = DCT_2D(R, Z, psiRZ)

        self.psi = lambda R, Z: self._dct(R, Z)
        modGradpsiSquared = (
            lambda R, Z: self._dct.ddR(R, Z) ** 2 + self._dct.ddZ(R, Z) ** 2
        )
        self.f_R = lambda R, Z: self._dct.ddR(R, Z) / modGradpsiSquared(R, Z)
        self.f_Z = lambda R, Z: self._dct.ddZ(R, Z) / modGradpsiSquared(R, Z)
        self.Bp_R = lambda R, Z: self._dct.ddZ(R, Z) / R
        self.Bp_Z = lambda R, Z: -self._dct.ddR(R, Z) / R
        self.d2psidR2 = self._dct.d2dR2
        self.d2psidZ2 = self._dct.d2dZ2
        self.d2psidRdZ = self._dct.d2dRdZ

    def findMinimum_1d(self, pos1, pos2, atol=1.0e-14):
        def coords(s):
            return pos1 + s * (pos2 - pos1)

        result = minimize_scalar(
            lambda s: self.psi(*coords(s)),
            method="bounded",
            bounds=(0.0, 1.0),
            options={"xatol": atol},
        )
        if result.success:
            return coords(result.x)
        else:
            raise SolutionError("findMinimum_1d failed")

    def findMaximum_1d(self, pos1, pos2, atol=1.0e-14):
        def coords(s):
            return pos1 + s * (pos2 - pos1)

        # minimize -f to find maximum
        result = minimize_scalar(
            lambda s: -self.psi(*coords(s)),
            method="bounded",
            bounds=(0.0, 1.0),
            options={"xatol": atol},
        )
        if result.success:
            return coords(result.x)
        else:
            raise SolutionError("findMaximum_1d failed")

    def findExtremum_1d(self, pos1, pos2, rtol=1.0e-5, atol=1.0e-14):
        smallDistance = 10.0 * rtol * calc_distance(pos1, pos2)

        minpos = self.findMinimum_1d(pos1, pos2, atol)
        if (
            calc_distance(pos1, minpos) > smallDistance
            and calc_distance(pos2, minpos) > smallDistance
        ):
            # minimum is not at either end of the interval
            return minpos, True

        maxpos = self.findMaximum_1d(pos1, pos2, atol)
        if (
            calc_distance(pos1, maxpos) > smallDistance
            and calc_distance(pos2, maxpos) > smallDistance
        ):
            return maxpos, False

        raise SolutionError("Neither minimum nor maximum found in interval")

    def findSaddlePoint(self, p1, p2, atol=2.0e-8):
        """
        Find a saddle point in the function self.psi atol is the tolerance on the
        position of the saddle point. p1, p2 are the positions of two adjacent corners of
        the square box to search for a saddle point in (the other corners p3 and p4 are
        taken to be to the right of the line p1->p2).
        """

        # Note: in this method, Point2D objects are used as displacement vectors as well
        # as as points.
        def dot(v1, v2):
            return v1.R * v2.R + v1.Z * v2.Z

        # length of sides of the square
        a = calc_distance(p1, p2)

        # unit vector along p1->p2 or p4->p3
        e1 = (p2 - p1) / a

        # unit vector along p2->p3 or p1->p4
        e2 = Point2D(e1.Z, -e1.R)

        p3 = p2 + a * e2
        p4 = p1 + a * e2

        # For the purposes of naming variables here, take p1 to be 'bottom left', p2 to
        # be 'top left', p3 to be 'top right' and p4 to be 'bottom right'
        posLeft, minLeft = self.findExtremum_1d(p1, p2)
        posTop, minTop = self.findExtremum_1d(p2, p3)
        posRight, minRight = self.findExtremum_1d(p3, p4)
        posBottom, minBottom = self.findExtremum_1d(p4, p1)

        assert (
            minTop == minBottom
        ), "if minumum is found at top, should also be found at bottom"
        assert (
            minLeft == minRight
        ), "if minumum is found at left, should also be found at right"
        assert (
            minTop != minLeft
        ), "if minimum is found at top, maximum should be found at left"

        if minTop:
            vertSearch = self.findMaximum_1d
        else:
            vertSearch = self.findMinimum_1d

        if minLeft:
            horizSearch = self.findMaximum_1d
        else:
            horizSearch = self.findMinimum_1d

        extremumVert = p3
        extremumHoriz = p1

        count = 0
        while calc_distance(extremumVert, extremumHoriz) > atol:
            count = count + 1

            extremumVert = vertSearch(posBottom, posTop, 0.5 * atol)
            # set position along e2 direction, keep position along e1 fixed (i.e. stay on
            # left or right edge)
            deltaz = dot(extremumVert - p1, e1)
            posLeft = p1 + deltaz * e1
            posRight = p4 + deltaz * e1

            extremumHoriz = horizSearch(posLeft, posRight, 0.5 * atol)
            # set position along e1 direction, keep position along e2 fixed (i.e. stay on
            # top or bottom edge)
            deltar = dot(extremumHoriz - p1, e2)
            posBottom = p1 + deltar * e2
            posTop = p2 + deltar * e2

        print("findSaddlePoint took", count, "iterations to converge")

        return (extremumVert + extremumHoriz) / 2.0

    def findRoots_1d(
        self, f, n, xmin, xmax, atol=2.0e-8, rtol=1.0e-5, maxintervals=1024
    ):
        """
        Find n roots of a scalar function f(x) in the range xmin<=x<=xmax
        Assume they're not too close to each other - exclude a small region around each
        found root when searching for more.
        """
        foundRoots = 0
        roots = []
        n_intervals = n
        while True:
            interval_points = numpy.linspace(xmin, xmax, n_intervals + 1)
            interval_f = f(interval_points)
            lucky_roots = numpy.where(interval_f == 0.0)
            if len(lucky_roots[0]) > 0:
                raise NotImplementedError(
                    "Don't handle interval points that happen to land " "on a root yet!"
                )
            intervals_with_roots = numpy.where(
                numpy.sign(interval_f[:-1]) != numpy.sign(interval_f[1:])
            )[0]
            if len(intervals_with_roots) >= n:
                break
            n_intervals *= 2
            if n_intervals > maxintervals:
                raise SolutionError(
                    "Could not find",
                    n,
                    "roots when checking",
                    maxintervals,
                    "intervals",
                )

        # find roots in the intervals
        for i in intervals_with_roots:
            root, info = brentq(
                f,
                interval_points[i],
                interval_points[i + 1],
                xtol=atol,
                full_output=True,
            )
            if not info.converged:
                raise SolutionError(
                    "Root finding failed in {"
                    + str(interval_points[i])
                    + ","
                    + str(interval_points[i + 1])
                    + "} with end values {"
                    + str(interval_f[i])
                    + ","
                    + str(interval_f[i + 1])
                )
            roots.append(root)
            foundRoots += 1

        if foundRoots > n:
            warnings.warn("Warning: found", foundRoots, "roots but expected only", n)

        return roots

    def wallPosition(self, s):
        """
        Get a position on the wall, where the distance along the wall is parameterized by
        0<=s<1
        """
        try:
            return Point2D(self.wallRInterp(s), self.wallZInterp(s))
        except AttributeError:
            # wall interpolation functions not created yet

            wall = deepcopy(self.wall)

            # make closed contour
            wall.append(wall[0])

            R = [p.R for p in wall]
            Z = [p.Z for p in wall]

            wallfraction = numpy.linspace(0.0, 1.0, len(wall))

            self.wallRInterp = interp1d(
                wallfraction, R, kind="linear", assume_sorted=True
            )
            self.wallZInterp = interp1d(
                wallfraction, Z, kind="linear", assume_sorted=True
            )

            return Point2D(self.wallRInterp(s), self.wallZInterp(s))

    def wallVector(self, s):
        """
        Get the vector along the wall at a point s, with the same parameterization as
        wallPosition.
        """
        try:
            return numpy.array(
                [self.wallVectorRComponent(s), self.wallVectorZComponent(s)]
            )
        except AttributeError:
            # wall vector interpolation functions not created yet
            Rcomponents = [
                self.wall[i + 1].R - self.wall[i].R for i in range(len(self.wall) - 1)
            ]
            Rcomponents.append(self.wall[0].R - self.wall[-1].R)
            Rcomponents.append(self.wall[1].R - self.wall[0].R)

            Zcomponents = [
                self.wall[i + 1].Z - self.wall[i].Z for i in range(len(self.wall) - 1)
            ]
            Zcomponents.append(self.wall[0].Z - self.wall[-1].Z)
            Zcomponents.append(self.wall[1].Z - self.wall[0].Z)

            wallfraction = numpy.linspace(0.0, 1.0, len(self.wall) + 1)

            # Vector along wall stays constant along each segment, as we assume the
            # segments are straight. Have calculated the vector at each vertex for the
            # following segment, so use 'previous' interpolation to just take the value
            # from the previous point
            self.wallVectorRComponent = interp1d(
                wallfraction, Rcomponents, kind="previous", assume_sorted=True
            )
            self.wallVectorZComponent = interp1d(
                wallfraction, Zcomponents, kind="previous", assume_sorted=True
            )

            return numpy.array(
                [self.wallVectorRComponent(s), self.wallVectorZComponent(s)]
            )

    def wallIntersection(self, p1, p2):
        """
        Find the intersection, if any, between the wall and the line between p1 and p2
        """
        closed_wall = self.wall + [self.wall[0]]
        wallarray = numpy.array([(p.R, p.Z) for p in closed_wall])
        intersects = find_intersections(wallarray, p1, p2)
        if intersects is not None:
            intersect = Point2D(*intersects[0, :])
            assert intersects.shape[0] < 3, "too many intersections with wall"
            if intersects.shape[0] > 1:
                second_intersect = Point2D(*intersects[1, :])
                assert (
                    numpy.abs(intersect.R - second_intersect.R) < intersect_tolerance
                    and numpy.abs(intersect.Z - second_intersect.Z)
                    < intersect_tolerance
                ), "Multiple intersections with wall found"
        else:
            intersect = None

        return intersect

    def make1dGrid(self, n, spacingFunc):
        """
        Make a 1d grid:
        - Start by generating grid of cell-face values, with values from spacingFunc.
        - Place cell-centre values half-way between cell-faces.

        spacingFunc should take an index between 0 and n, and returns the desired
        coordinate value.
        """
        face_vals = [spacingFunc(i) for i in range(n + 1)]

        result = numpy.zeros(2 * n + 1)
        result[::2] = face_vals
        result[1::2] = 0.5 * (result[:-1:2] + result[2::2])

        return result

    def getPolynomialGridFunc(
        self, n, lower, upper, *, grad_lower=None, grad_upper=None
    ):
        """
        A polynomial function with value 'lower' at 0 and 'upper' at n, used to
        non-uniformly place grid point values in index space.
        Optionally matches the gradient grad_lower at the lower end and grad_upper at the
        upper end.
        If the gradient is specified, the second derivative is set to zero, to ensure
        that the derivative of the grid spacing is zero, and so the grid spacing will be
        smooth across boundaries.
        Linear if neither gradient given, cubic if one given, quintic if both given.
        """
        if grad_lower is None and grad_upper is None:
            return lambda i: lower + (upper - lower) * i / n
        elif grad_lower is None:
            # psi(i) = a*i^3 + b*i^2 + c*i + d
            # psi(0) = lower = d
            # psi(n) = upper = a*n^3 + b*n^2 + c*n + d
            # dpsidi(n) = grad_upper = 3*a*n^2 + 2*b*n + c
            # d2psidi2(n) = 0 = 6*a*n + 2*b
            # a = -b/(3*n)
            # grad_upper = -b*n + 2*b*n + c
            #            = b*n + c
            # b = (grad_upper - c)/n
            # upper = -(grad_upper - c)*n/3 + (grad_upper - c)*n + c*n + d
            #       = 2*grad_upper*n/3 + c*n/3 + d
            # c = 3.*(upper - d - 2.*grad_upper*n/3.)/n
            d = lower
            c = 3.0 * (upper - d - 2.0 * grad_upper * n / 3.0) / n
            b = (grad_upper - c) / n
            a = -b / (3.0 * n)
            return lambda i: a * i ** 3 + b * i ** 2 + c * i + d
        elif grad_upper is None:
            # psi(i) = a*i^3 + b*i^2 + c*i + d
            # psi(0) = lower = d
            # psi(n) = upper = a*n^3 + b*n^2 + c*n + d
            # dpsidi(0) = grad_lower = c
            # d2psidi2(0) = 0 = 2*b
            d = lower
            c = grad_lower
            b = 0.0
            a = (upper - b * n ** 2 - c * n - d) / n ** 3
            return lambda i: a * i ** 3 + b * i ** 2 + c * i + d
        else:
            # psi(i) = a*i^5 + b*i^4 + c*i^3 + d*i^2 + e*i + f
            # psi(0) = lower = f
            # dpsidi(0) = grad_lower = e
            # d2psidi2(0) = 0 = 2*d
            # psi(n) = upper = a*n^5 + b*n^4 + c*n^3 + e*n + f
            # dpsidi(n) = grad_upper = 5*a*n^4 + 4*b*n^3 + 3*c*n^2 + e
            # d2psidi2(n) = 0 = 20*a*n^3 + 12*b*n^2 + 6*c*n
            # grad_upper = (4-3)*b*n^3 + (3-3/2)*c*n^2 + e
            #            = b*n^3 + 3*c*n^2/2 + e
            # upper = (1-3/5)*b*n^4 + (1-3/10)*c*n^3 + e*n + f
            #       = 2*b*n^4/5 + 7*c*n^3/10 + e*n + f
            # n*grad_upper - 5*upper/2 = (3/2 - 7/4)*c*n^3 + (1-5/2)*e*n - 5*f/2
            #                          = -c*n^3/4 - 3*e*n/2 - 5*f/2
            # c = 4*(5*upper/2 - n*grad_upper - 3*e*n/2 - 5*f/2)/n^3
            f = lower
            e = grad_lower
            d = 0.0
            c = (
                4.0
                * (
                    5.0 * upper / 2.0
                    - n * grad_upper
                    - 3.0 * e * n / 2.0
                    - 5.0 * f / 2.0
                )
                / n ** 3
            )
            b = (grad_upper - 3.0 * c * n ** 2 / 2.0 - e) / n ** 3
            a = -(6.0 * b * n + 3 * c) / (10.0 * n ** 2)
            return (
                lambda i: a * i ** 5 + b * i ** 4 + c * i ** 3 + d * i ** 2 + e * i + f
            )

    def plotPotential(
        self,
        Rmin=None,
        Rmax=None,
        Zmin=None,
        Zmax=None,
        npoints=100,
        ncontours=40,
        labels=True,
        axis=None,
        **kwargs,
    ):
        from matplotlib import pyplot

        if Rmin is None:
            Rmin = self.Rmin
        if Rmax is None:
            Rmax = self.Rmax
        if Zmin is None:
            Zmin = self.Zmin
        if Zmax is None:
            Zmax = self.Zmax

        R = numpy.linspace(Rmin, Rmax, npoints)
        Z = numpy.linspace(Zmin, Zmax, npoints)

        if axis is None:
            axis = pyplot.axes(aspect="equal")

        contours = axis.contour(
            R,
            Z,
            self.psi(R[:, numpy.newaxis], Z[numpy.newaxis, :]).T,
            ncontours,
            **kwargs,
        )
        if labels:
            pyplot.clabel(contours, inline=False, fmt="%1.3g")

        return axis

    def plotWall(self, axis=None):
        if self.wall:
            wall_R = [p.R for p in self.wall]
            wall_Z = [p.Z for p in self.wall]

            # make contours closed
            wall_R.append(wall_R[0])
            wall_Z.append(wall_Z[0])

            if axis is None:
                from matplotlib import pyplot

                axis = pyplot.plot(wall_R, wall_Z, "k-", linewidth=2)
            else:
                axis.plot(wall_R, wall_Z, "k-", linewidth=2)

            return axis

    def plotSeparatrix(self):
        from matplotlib import pyplot

        for region in self.regions.values():
            R = [p.R for p in region]
            Z = [p.Z for p in region]
            pyplot.scatter(R, Z, marker="x", label=region.name)

    def _getOptionsAsString(self):
        import yaml

        result = ""
        result += yaml.dump(self.equilibOptions)

        mesh_options_dict = {"Mesh": {}}
        m = mesh_options_dict["Mesh"]
        for key, val in self.user_options.items():
            if val is not None:
                m[key] = str(val)

        result += yaml.dump(mesh_options_dict)

        return result

    def saveOptions(self, filename="hypnotoad_options.yaml"):
        with open(filename, "x") as f:
            f.write(self._getOptionsAsString())