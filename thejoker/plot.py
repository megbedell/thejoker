# Third-party
from astropy.time import Time
import astropy.units as u
import numpy as np

__all__ = ['plot_rv_curves']


def plot_rv_curves(samples, t_grid, n_plot=None, rv_unit=None, data=None,
                   ax=None, plot_kwargs=dict(), data_plot_kwargs=dict(),
                   add_labels=True, relative_to_t0=False):
    """
    Plot radial velocity curves for the input set of orbital parameter
    samples over the input grid of times.

    Parameters
    ----------
    samples : :class:`~thejoker.sampler.JokerSamples`
        Posterior samples from The Joker.
    t_grid : array_like, `~astropy.time.Time`
        Array of times. Either in BMJD or as an Astropy time object.
    n_plot : int, optional
        The maximum number of samples to plot. Defaults to 128.
    rv_unit : `~astropy.units.UnitBase`, optional
        The units to use when plotting RV's.
    data : `~thejoker.data.RVData`, optional
        Over-plot the data as well.
    ax : `~matplotlib.Axes`, optional
        A matplotlib axes object to plot on to. If not specified, will
        create a new figure and plot on that.
    plot_kwargs : dict, optional
        Passed to `matplotlib.pyplot.plot()`.
    data_plot_kwargs : dict, optional
        Passed to `thejoker.data.RVData.plot()`.
    add_labels : bool, optional
        Add labels to the axes or not.
    relative_to_t0 : bool, optional
        Plot the time axis relative to ``samples.t0``.

    Returns
    -------
    fig : `~matplotlib.Figure`

    """

    if ax is None:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 1)
    else:
        fig = ax.figure

    if not isinstance(t_grid, Time): # Assume BMJD
        t_grid = Time(t_grid, format='mjd', scale='tcb')

    if n_plot is None:
        n_plot = len(samples)
    n_plot = min(n_plot, len(samples))

    # scale the transparency of the lines
    Q = 4. # HACK
    line_alpha = 0.05 + Q / (n_plot + Q)

    if rv_unit is None:
        rv_unit = u.km/u.s

    # default plotting style
    style = plot_kwargs.copy()
    style.setdefault('linestyle', '-')
    style.setdefault('alpha', line_alpha)
    style.setdefault('marker', '')
    style.setdefault('color', '#555555')
    style.setdefault('rasterized', True)

    # plot orbits over the data
    model_rv = np.zeros((n_plot, len(t_grid)))
    for i in range(n_plot):
        orbit = samples.get_orbit(i)
        model_rv[i] = orbit.radial_velocity(t_grid).to(rv_unit).value

    bmjd = t_grid.tcb.mjd
    if relative_to_t0:
        if samples.t0 is None:
            raise ValueError('Input samples object has no epoch .t0')
        bmjd = bmjd - samples.t0.tcb.mjd

    ax.plot(bmjd, model_rv.T, **style)

    if data is not None:
        data_style = data_plot_kwargs.copy()
        data_style.setdefault('rv_unit', rv_unit)
        data_style.setdefault('markersize', 4.)

        if data_style['rv_unit'] != rv_unit:
            raise u.UnitsError("Data plot units don't match rv_unit!")

        data.plot(ax=ax, relative_to_t0=relative_to_t0, **data_style)

        _rv = data.rv.to(rv_unit).value
        drv = _rv.max() - _rv.min()
        ax.set_ylim(_rv.min() - 0.2*drv, _rv.max() + 0.2*drv)

    ax.set_xlim(bmjd.min(), bmjd.max())
    if add_labels:
        ax.set_xlabel('BMJD')
        ax.set_ylabel('RV [{}]'
                      .format(rv_unit.to_string(format='latex_inline')))

    return fig
