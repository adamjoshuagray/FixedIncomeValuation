from typing import List, Callable
from bond import FixedRateACGB, Coupon
from datetime import date, timedelta
from scipy.optimize import least_squares
from scipy.interpolate import CubicSpline
from numpy import exp, log, linspace



class DiscountFitOptions:
    """Options for how the fit procedure should run.
    """
    def __init__(self):
        self.knot_count = 5
        """The number of knots to use in the cubic splite fit."""
        self.extenion_days = 100
        """The number of days before the first bond and after the 
        last bond to extend the curve.
        """


def _date_to_year_fraction_act_365(today: date, future_date: date) -> float:
    """Converts two dates into a year fraction interval where 1 year = 1.

    Args:
        today (date): The reference date to start from.
        future_date (date): The date to caulcate up to.

    Returns:
        float: A fraction of a year representation of time.
    """
    days = days = (future_date - today).days
    year_frac = days / 365
    return year_frac

def _year_fraction_act_365_to_date(today: date, year_fraction: date) -> float:
    """Adds a year fraction to a start date and return the date.

    Args:
        today (date): The reference / start date to calculate from.
        year_fraction (date): The amount of a year to add.

    """
    days = round(year_fraction * 365)
    return today + timedelta(days=days)

def discount_to_yield(discount: float, future_date: date, today: date) -> float:
    year_frac = _date_to_year_fraction_act_365(today, future_date)
    return pow(discount, -1.0 / year_frac) - 1

def fit_discount_curve(bonds: List[FixedRateACGB],
                       options: DiscountFitOptions,
                       today: date) -> Callable[[date], float]: 
    """Fits a discount curve to a list of given bonds.

    Args:
        bonds (List[FixedRateACGB]): The bonds to use for fitting.
        options (DiscountFitOptions): The fitting options to use.
        today (date): The start state of the discount curve.

    Returns:
        Callable[[date], float]: A function P(date) -> (discount rate)
            which represents the value of a zero coupon bond.
    """

    sorted_bonds = list(sorted(bonds, key=lambda b: b.maturity))
    first_maturity = sorted_bonds[0].maturity
    last_maturity = sorted_bonds[-1].maturity
    
    curve_start = first_maturity - timedelta(days = options.extenion_days)
    curve_end = last_maturity + timedelta(days = options.extenion_days)

    if curve_start < today:
        curve_start = today

    cv_start_yr_frac = _date_to_year_fraction_act_365(today, curve_start)
    cv_end_yr_frac = _date_to_year_fraction_act_365(today, curve_end)

    knot_locations = linspace(cv_start_yr_frac, cv_end_yr_frac, options.knot_count)
    
    initial_guess = [0.01] * options.knot_count
    
    def _resid(knots):
        curve = CubicSpline(knot_locations, knots)
        date_curve = lambda dt: curve(_date_to_year_fraction_act_365(today, dt))
        residuals = [b.calculate_dirty_value(date_curve, today) - b.market_dirty_price for b in sorted_bonds]
        return residuals


    fitted_knots = least_squares(_resid, initial_guess).x
    
    fitted_curve = CubicSpline(knot_locations, fitted_knots)
    fitted_dt_curve = lambda dt: fitted_curve(_date_to_year_fraction_act_365(today, dt))
    return fitted_dt_curve
