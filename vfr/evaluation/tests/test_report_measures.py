from vfr.evaluation.eval_positional_repeatability import get_angular_error
from vfr.evaluation.measures import get_measures

if __name__ == "__main__":

    list_of_errors = ( 0.0087,
	0.0144,
	0.0123,
	0.006,
	0.0051,
	0.0056,
	0.0091,
	0.0154,
	0.0235,
	0.0205,
	0.0274,
	0.023,
	0.0241,
	0.0319,
	0.0375,
	0.0399,
	0.0379,
	0.0483,
	0.0528,
	0.0359,
	0.0261,
	0.0237,
	0.0257,
	0.0241,
	0.0268,
	0.0352,
	0.0288,
	0.0205,
	0.0136,
	0.0167,
	0.0146,
	0.0285,
	0.0364,
	0.0303,
	0.0355,
	0.0283,
	0.0256,
	0.0116,
	0.009,
	0.0065,
        )

    measures = get_measures( list_of_errors )

    print( measures )
    print( " " )

    dict_of_coords = { (1.0, 1.0, 1, 1, 1) : (1.0, 1.0, 0.2, 2.0, 1.0, 0.5),
                       (2.0, 1.0, 1, 1, 2) : (2.0, 1.5, 0.2, 3.0, 1.5, 0.5),
                       (3.0, 1.0, 1, 1, 3) : (3.0, 2.0, 0.2, 4.0, 2.0, 0.5),
                       (4.0, 1.0, 1, 1, 3) : (4.0, 2.5, 0.2, 5.0, 2.5, 0.5),
                       (1.0, 2.0, 1, 1, 3) : (5.0, 3.0, 0.2, 6.0, 3.0, 0.5),
                       (1.0, 2.0, 1, 1, 3) : (6.0, 3.5, 0.2, 7.0, 3.5, 0.5),
                       (1.0, 3.0, 1, 1, 3) : (7.0, 4.0, 0.2, 8.0, 4.0, 0.5),
                       (1.0, 4.0, 1, 1, 3) : (8.0, 4.5, 0.2, 9.0, 4.5, 0.5),
                     }

    max_at_angle, measures = get_angular_error( dict_of_coords, 0 )

    print( max_at_angle )
    print( measures )

    max_at_angle, measures = get_angular_error( dict_of_coords, 1 )

    print( max_at_angle )
    print( measures )

