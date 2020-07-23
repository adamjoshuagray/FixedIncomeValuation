from datetime import date, timedelta
from typing import List, Callable


class Coupon:
    """Represents a coupon paid by a bond."""
    def __init__(self, amount: float, ex_date: date, payment_date: date):
        """Creates a coupon for a fixed rate bond with given paramters.

        Args:
            amount (float): The amount of the coupon.

            ex_date (date): The ex-date of the coupon.
                This is the date after which the bond trades without
                entitlement to this coupon.

            payment_date (date): The actual date that the coupon is paid.
        """
        self.ex_date = ex_date
        self.payment_date = payment_date
        self.coupon_amount = amount


class FixedRateACGB:
    """This class represents a government bond which pays predetermined
    coupons on predetermined dates.
    """

    def __init__(self, principle: float,
                 coupons: List[Coupon], maturity: date):
        """Creates a goverment bond with specified parameters.

        Args:
            principle (float): The face value of the bond which is
                to be repaid on expiry.

            coupons (List[Coupon]): A list of coupons which are to be
                paid over the life of the bond.

            maturity: The date on which the principle / face value is repaid.
        """
        self.principle = principle
        self.coupons = coupons
        self.maturity = maturity
        self._market_dirty_price = 0

    @property
    def market_value(self) -> float:
        """Gets the current market value of the bond.

        Returns:
            float: The current market value.
        """
        return self._market_dirty_price

    @market_value.setter
    def market_dirty_price(self, value: float):
        """Sets the current market value of the bond.

        Args:
            value (float): The current market value.
        """
        self._market_dirty_price = value

    def calculate_dirty_value(self, discount_curve: Callable[[date], float],
                        today: date) -> float:
        """Calculates the theoretical dirty value of a bond given a particular
        discount curve.

        The theoretical is V = \\sum_i c_i d_i
        where c_i is the ith coupon and d_i is the associated discount
        factor associated with the coupon.
        d_i is calculated as discount_curve(coupon_payment_date)

        Args:
            discount_curve ([type]): A function which takes a date and
                returns the associated discount factor required for
                that date.

            today (date): The date to use fo including or excluding
                coupons.
        """

        future_coupons = (c for c in self.coupons if c.ex_date > today)
        discounted_coupon_value = sum(
            discount_curve(c.payment_date) * c.coupon_amount
            for c in future_coupons
            )
        discounted_face_value = discount_curve(self.maturity) * self.principle
        return discounted_coupon_value + discounted_face_value

    @staticmethod
    def _business_date(reference_date: date) -> date:
        """Converts a date to the first available business date.

        FIXME: This just assumes all weekdays are business dates 
            and weekends are not.

        Args:
            reference_date (date): The date to convert to the next 
                business date.

        Returns:
            date: If reference_date is a business date just return
                reference date, otherwise return the next 
                business date.
        """        
        if reference_date.weekday() > 4:
            return FixedRateACGB._business_date(
                reference_date + timedelta(days = 1))
        return reference_date

    @staticmethod
    def construct_yearly_coupon_series(first_pay_date: date, 
        last_pay_date: date, rate: float, 
        principle: float) -> List[Coupon]:
        """Constructs a series of anual coupons starting
        on the first pay date and ending on or before the last pay date.

        NOTE: Assumes that exdates are 9 days before the payment date.

        Args:
            first_pay_date (date): The first day on which a coupon is paid.
            last_pay_date (date): The last day on which a coupon is paid.
            rate (float): The coupon rate. 
                On principle of 100, 0.03 corresponds to 3.
            principle (float): The principle / par value of the bond.

        Returns:
            List[Coupon]: A list of coupons which 
        """        
        coupons = []
        coupon_date = first_pay_date
        amount = principle * rate
        while coupon_date <= last_pay_date:
            ex_date = FixedRateACGB._business_date(
                coupon_date - timedelta(days = 9))
            payment_date = FixedRateACGB._business_date(coupon_date)
            coupons.append(Coupon(amount, ex_date, payment_date))
            coupon_date = date(coupon_date.year + 1, 
                coupon_date.month, coupon_date.day)
        return coupons

    @staticmethod
    def construct(first_coupon_pay_date: date, 
        second_coupon_pay_date: date, maturity_date: date, 
        coupon_rate: float, principle: float):
        """Creates a FixedRateACGB based on some minimal 
        parameters which describe the bond.

        Args:
            first_coupon_pay_date (date): The first date on which 
                coupons are paid.
            second_coupon_pay_date (date): The second date on which
                coupons are paid.
            maturity_date (date): They date on which the last coupon
                payment is made and the principle value is repaid.
            coupon_rate (float): The annualized coupon rate for the bond.
            principle (float): The par value of the bond.

        Returns:
            FixedRateACGB: [description]
        """
        coupons_a = FixedRateACGB.construct_yearly_coupon_series(
            first_coupon_pay_date, maturity_date, 
            coupon_rate / 2.0, principle)
        coupons_b = FixedRateACGB.construct_yearly_coupon_series(
            second_coupon_pay_date, maturity_date, 
            coupon_rate / 2.0, principle)

        return FixedRateACGB(principle, coupons_a + coupons_b, maturity_date)