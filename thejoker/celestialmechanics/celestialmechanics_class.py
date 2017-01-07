from __future__ import division, print_function

# Third-party
import astropy.time as at
import astropy.units as u
from astropy.utils.misc import isiterable

# Project
from .celestialmechanics import rv_from_elements
from ..util import find_t0

__all__ = ['SimulatedRVOrbit']

class SimulatedRVOrbit(object):
    """

    Parameters
    ----------
    pars : `thejoker.OrbitalParams`

    """
    @u.quantity_input(P=u.day, K=u.km/u.s,
                      phi0=u.radian, omega=u.radian)
    def __init__(self, P, K, ecc, phi0, omega):
        self.P = P
        self.K = K
        self.ecc = float(ecc)
        self.phi0 = phi0
        self.omega = omega

    def _t0(self, epoch_day):
        return find_t0(self.phi0.to(u.radian).value,
                       self.P.to(u.day).value,
                       epoch_day)

    def t0(self, epoch):
        """
        Un-mod the phase at pericenter ``phi0`` to a time closest to the
        specified epoch.

        Parameters
        ----------
        epoch : `~astropy.time.Time`
            Reference time to get the pericenter time ``t0`` relative to.

        Returns
        -------
        t0 : `~astropy.time.Time`
            Pericenter time closest to input epoch.

        """
        epoch_mjd = epoch.tcb.mjd
        return at.Time(self._t0(epoch_mjd), scale='tcb', format='mjd')

    def _generate_rv_curve(self, t):
        """
        Parameters
        ----------
        t : array_like, `~astropy.time.Time`
            Array of times. Either in BJD or as an Astropy time.

        Returns
        -------
        rv : numpy.ndarray
        """

        if isinstance(t, at.Time):
            _t = t.tcb.mjd
        else:
            _t = t

        rv = rv_from_elements(times=_t,
                              P=self.P.to(u.day).value,
                              K=self.K.to(u.m/u.s).value,
                              e=self.ecc,
                              omega=self.omega.to(u.radian).value,
                              phi0=self.phi0.to(u.radian).value)

        return rv

    def generate_rv_curve(self, t):
        """
        Parameters
        ----------
        t : array_like, `~astropy.time.Time`
            Time array. Either in BMJD or as an Astropy time.

        Returns
        -------
        rv : astropy.units.Quantity [speed]
        """
        rv = self._generate_rv_curve(t)
        return (rv*u.m/u.s).to(u.km/u.s)

    def __call__(self, t):
        return self.generate_rv_curve(t)

    def plot(self, t, ax=None, rv_unit=None,
             t_format='mjd', t_scale='tcb', **kwargs):
        """
        Plot the RV curve at the specified times.

        Parameters
        ----------
        t : array_like, `~astropy.time.Time`
            Time array. Either in BMJD or as an Astropy time.
        ax : `~matplotlib.axes.Axes` (optional)
            The axis to draw on (default is to grab the current
            axes using `~matplotlib.pyplot.gca`).
        rv_unit : `~astropy.units.UnitBase` (optional)
            Units to plot the radial velocities in (default is km/s).
        t_format : str (optional)
            Used to convert the `~astropy.time.Time` object to a numeric
            value for plotting (default is 'mjd').
        t_scale : str (optional)
            Used to convert the `~astropy.time.Time` object to a numeric
            value for plotting (default is 'tcb', barycentric).

        Returns
        -------
        ax : `~matplotlib.axes.Axes`
            The matplotlib axes object that the RV curve was drawn on.

        """

        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        if rv_unit is None:
            rv_unit = u.km/u.s

        style = kwargs.copy()
        style.setdefault('linestyle', '-')
        style.setdefault('alpha', 0.5)
        style.setdefault('marker', None)
        style.setdefault('color', '#de2d26')

        if not isinstance(t, at.Time):
            t = at.Time(t, format=t_format, scale=t_scale)
        rv = self.generate_rv_curve(t).to(rv_unit).value

        _t = getattr(getattr(t, t_scale), t_format)
        ax.plot(_t, rv, **style)

        return ax
