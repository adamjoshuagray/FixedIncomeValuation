from unittest import TestCase, main
from bond import Coupon, FixedRateACGB
from discount_curve import fit_discount_curve, DiscountFitOptions, discount_to_yield
from datetime import date

class TestBondMethods(TestCase):

    def test_coupon_generation(self):
        """Test that coupons are generated on the correct dates
        with the correct ammount.
        """        
        coupons = FixedRateACGB.construct_yearly_coupon_series(
            date(2020, 11, 21), date(2030, 11, 21), 0.01, 100)
        
        self.assertEqual(len(coupons), 11)
        for c in coupons:
            self.assertAlmostEqual(1.0, c.coupon_amount)
            self.assertTrue(c.payment_date.weekday() <= 4)
            self.assertTrue(c.ex_date.weekday() <= 4)

        self.assertEqual(coupons[0].payment_date, date(2020, 11, 23))
        self.assertEqual(coupons[0].ex_date, date(2020, 11, 12))

    def test_bond_generation(self):
        """Test that a bond is generated with the correct coupons.
        """
        bond = FixedRateACGB.construct(
            date(2020, 11, 21), date(2021, 5, 21), date(2030, 5, 21),
            0.01, 100)
        self.assertEqual(20, len(bond.coupons))
        self.assertEqual(date(2030, 5, 21), bond.coupons[-1].payment_date)
        for c in bond.coupons:
            self.assertAlmostEqual(0.5, c.coupon_amount)

    def test_basic_pricing(self):
        """Test basic pricing conditions (extremes)
        """
        bond = FixedRateACGB.construct(
            date(2020, 11, 21), date(2021, 5, 21), date(2030, 5, 21),
            0.01, 100)
        # Flat zero interest rate curve
        dummy_curve = lambda dt: 1
        # At 0 interest rate the price of the bond is 
        # just the par + sum of coupons
        self.assertAlmostEqual(100 + 0.5 * 20, 
            bond.calculate_dirty_value(dummy_curve, date(2020, 7, 20)))

        # Should result in the price just getting multiplied by 0.99
        dummy_curve = lambda dt: 0.99
        self.assertAlmostEqual((100 + 0.5 * 20) * 0.99, 
            bond.calculate_dirty_value(dummy_curve, date(2020, 7, 20)))

        # Discount curve works when not flat
        dummy_curve = lambda dt: 0.99 if dt < date(2025, 1, 1) else 1
        self.assertAlmostEqual((0.5 * 9 * 0.99) + (0.5 * 11 * 1.0) + 100, 
                bond.calculate_dirty_value(dummy_curve, date(2020, 7, 20)))


    def test_fit(self):
        """Test fitting against sample market values.
        """
        gsbu_20 = FixedRateACGB.construct(date(2015, 5, 21), 
            date(2015, 11, 21), date(2020, 11, 21), 0.015, 100)
        gsbu_20.market_dirty_price = 101.066

        gsbi_21 = FixedRateACGB.construct(date(2007, 5, 15), 
            date(2015, 11, 15), date(2021, 5, 15), 0.0575, 100)
        gsbi_21.market_dirty_price = 105.640
        
        gsbm_22 = FixedRateACGB.construct(date(2010, 7, 15), 
            date(2011, 1, 15), date(2022, 7, 15), 0.0575, 100)
        gsbm_22.market_dirty_price = 111.177

        gsbu_22 = FixedRateACGB.construct(date(2017, 5, 21), 
            date(2017, 11, 21), date(2022, 11, 21), 0.0225, 100)
        gsbu_22.market_dirty_price = 105.213

        gsbg_23 = FixedRateACGB.construct(date(2011, 10, 21), 
            date(2012, 4, 21), date(2023, 4, 21), 0.055, 100)
        gsbg_23.market_dirty_price = 115.900

        gsbg_24 = FixedRateACGB.construct(date(2012, 10, 21), 
            date(2013, 4, 21), date(2024, 4, 21), 0.0275, 100)
        gsbg_24.market_dirty_price = 109.920

        gsbu_24 = FixedRateACGB.construct(date(2020, 5, 21), 
            date(2020, 11, 21), date(2024, 11, 21), 0.0025, 100)
        gsbu_24.market_dirty_price = 99.699 

        gsbg_25 = FixedRateACGB.construct(date(2013, 10, 21), 
            date(2014, 4, 21), date(2025, 4, 21), 0.0325, 100)
        gsbg_25.market_dirty_price = 114.365

        gsbg_26 = FixedRateACGB.construct(date(2014, 4, 21), 
            date(2014, 10, 21), date(2026, 4, 21), 0.0425, 100)
        gsbg_26.market_dirty_price = 122.362

        gsbg_27 = FixedRateACGB.construct(date(2012, 4, 21), 
            date(2012, 10, 21), date(2027, 4, 21), 0.0475, 100)
        gsbg_27.market_dirty_price =  128.980

        gsbu_27 = FixedRateACGB.construct(date(2016, 5, 21), 
            date(2016, 11, 21), date(2027, 11, 21), 0.0275, 100)
        gsbu_27.market_dirty_price =  115.380 

        gsbi_28 = FixedRateACGB.construct(date(2016, 5, 21), 
            date(2016, 11, 21), date(2028, 11, 21), 0.0225, 100)
        gsbi_28.market_dirty_price =  112.030 

        gsbi_28 = FixedRateACGB.construct(date(2017, 5, 21), 
            date(2017, 11, 21), date(2028, 5, 21), 0.0275, 100)
        gsbi_28.market_dirty_price =  112.030

        bond_universe = [gsbu_20, 
             gsbi_21, 
             gsbm_22, gsbu_22, 
             gsbg_23, 
             gsbg_24, gsbu_24, 
             gsbg_25, 
             gsbg_26, 
             gsbg_27, gsbu_27,
        ]

        # fit with 5 knots
        dfo = DiscountFitOptions()
        dfo.knot_count = 5
        discount_curve = fit_discount_curve(bond_universe, 
            dfo, date(2020, 7, 23))

        # check that we are within 20c of the the market price
        for b in bond_universe:
            self.assertAlmostEqual(b.calculate_dirty_value(discount_curve, date(2020, 7, 23)), b.market_dirty_price, delta=0.2)

        self.assertAlmostEqual(discount_to_yield(discount_curve(date(2023, 1, 1)), date(2023, 1, 1), date(2020, 7, 23)), 0.0020, delta=0.0001)
        

        # fit with 10 knots
        dfo.knot_count = 10
        discount_curve = fit_discount_curve(bond_universe, 
            dfo, date(2020, 7, 23))
        
        # check that we are within 1c of the the market price
        for b in bond_universe:
            self.assertAlmostEqual(b.calculate_dirty_value(discount_curve, date(2020, 7, 23)), b.market_dirty_price, delta=0.01)

        self.assertAlmostEqual(discount_to_yield(discount_curve(date(2023, 1, 1)), date(2023, 1, 1), date(2020, 7, 23)), 0.0018, delta=0.0001)

if __name__ == '__main__':
    main()