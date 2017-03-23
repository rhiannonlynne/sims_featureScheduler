import numpy as np
import healpy as hp
from .utils import treexyz, hp_kd_tree, rad_length, set_default_nside, read_fields

default_nside = set_default_nside()


def wrapRADec(ra, dec):
    # XXX--from MAF, should put in general utils
    """
    Wrap RA into 0-2pi and Dec into +/0 pi/2.

    Parameters
    ----------
    ra : numpy.ndarray
        RA in radians
    dec : numpy.ndarray
        Dec in radians

    Returns
    -------
    numpy.ndarray, numpy.ndarray
        Wrapped RA/Dec values, in radians.
    """
    # Wrap dec.
    low = np.where(dec < -np.pi / 2.0)[0]
    dec[low] = -1 * (np.pi + dec[low])
    ra[low] = ra[low] - np.pi
    high = np.where(dec > np.pi / 2.0)[0]
    dec[high] = np.pi - dec[high]
    ra[high] = ra[high] - np.pi
    # Wrap RA.
    ra = ra % (2.0 * np.pi)
    return ra, dec


def rotate_ra_dec(ra, dec, ra_target, dec_target, init_rotate=0.):
    """
    Rotate ra and dec coordinates to be centered on a new dec.

    Inputs
    ------
    ra : float or np.array
        RA coordinate(s) to be rotated in radians
    dec : float or np.array
        Dec coordinate(s) to be rotated in radians
    ra_rotation : float
        RA distance to rotate in radians
    dec_target : float
        Dec distance to rotate in radians
    init_rotate : float (0.)
        The amount to rotate the points around the x-axis first (radians).
    """
    # point (ra,dec) = (0,0) is at x,y,z = 1,0,0

    x, y, z = treexyz(ra, dec)

    # Rotate around the x axis to start
    xp = x
    if init_rotate != 0.:
        c_i = np.cos(init_rotate)
        s_i = np.sin(init_rotate)
        yp = c_i*y - s_i*z
        zp = s_i*y + c_i*z
    else:
        yp = y
        zp = z

    theta_y = dec_target
    c_ty = np.cos(theta_y)
    s_ty = np.sin(theta_y)

    # Rotate about y
    xp2 = c_ty*xp + s_ty*zp
    zp2 = -s_ty*xp + c_ty*zp

    # Convert back to RA, Dec
    ra_p = np.arctan2(yp, xp2)
    dec_p = np.arcsin(zp2)

    # Rotate to the correct RA
    ra_p += ra_target

    ra_p, dec_p = wrapRADec(ra_p, dec_p)

    return ra_p, dec_p


class pointings2hp(object):
    """
    Convert a list of telescope pointings and convert them to a pointing map
    """
    def __init__(self, nside, radius=1.75):
        """

        """
        self.tree = hp_kd_tree(nside=nside, leafsize=200)
        self.nside = nside
        self.rad = rad_length(radius)
        self.bins = np.arange(hp.nside2npix(nside)+1)-.5

    def __call__(self, ra, dec, stack=True):
        """
        similar to utils.hp_in_lsst_fov, but can take a arrays of ra,dec.

        Parameters
        ----------
        ra : array_like
            RA in radians
        dec : array_like
            Dec in radians

        Returns
        -------
        result : healpy map
            The number of times each healpxel is observed by the given pointings
        """
        xs, ys, zs = treexyz(ra, dec)
        coords = np.array((xs, ys, zs)).T
        # This seems to fail for more than 200 pointings?
        indx = self.tree.query_ball_point(coords, self.rad)
        # Convert array of lists to single array
        if stack:
            indx = np.hstack(indx)
            result, bins = np.histogram(indx, bins=self.bins)
        else:
            result = indx
        
        return result


class hpmap_cross(object):
    """
    Find the cross-correlation of a healpix map and a bunch of rotated pointings
    """
    def __init__(self, nside=default_nside, radius=1.75):
        """

        """

        # XXX -- should I shrink the radius slightly to get rid of overlap? That would be clever!
        self.p2hp = pointings2hp(nside=nside, radius=radius)
        # Load up a list of pointings, chop them down to a small block

        # XXX--Should write code to generate a new tellelation so we know where it came from,
        # not just a random .dat file that's been floating around! 
        fields = read_fields()
        good = np.where((fields['RA'] > np.radians(360.-15.)) | (fields['RA'] < np.radians(15.)))
        fields = fields[good]
        good = np.where(np.abs(fields['dec']) < np.radians(15.))
        fields = fields[good]
        self.ra = fields['RA']
        self.dec = fields['dec']

    def __call__(self, inmap, ra_rot, dec_rot, im_rot, return_pointings_map=False):
        """
        Parameters
        ----------
        inmap : numpy array
             A Healpixel map.
        ra_rot : float
            Amount to rotate the fields in RA (radians)
        dec_rot : float
            Amount to rotate the fields in Dec (radians)
        im_rot : float
            Initial rotation to apply to fields (radians)
        return_pointings_map : bool (False)
            If set, return the overlapping fields and the resulting observing helpix map

        Returns
        -------
        cross_corr : float
            If return_pointings_map is False, return the sum of the pointing map multipled 
            with the 
        """
        # XXX-check the nside 
        # Rotate pointings to desired position
        final_ra, final_dec = rotate_ra_dec(self.ra, self.dec, ra_rot, dec_rot, init_rotate=im_rot)
        # Find the number of observations at each healpixel
        obs_map = self.p2hp(final_ra, final_dec)
        good = np.where(inmap != hp.UNSEEN)[0]

        # Should check that the pointings cover the area where I want them.

        if return_pointings_map:
            obs_indx = self.p2hp(final_ra, final_dec, stack=False)
            good_pointings = np.array([True if np.intersect1d(indxes, good).size > 0
                                      else False for indxes in obs_indx])
            obs_map = self.p2hp(final_ra[good_pointings], final_dec[good_pointings])
            return final_ra[good_pointings], final_dec[good_pointings], obs_map
        else:
            result = np.sum(inmap[good] * obs_map[good])
            return result








