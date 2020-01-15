def foo():
    if julian == -1 and week_of_year != -1 and weekday != -1:
        first_weekday = datetime_date(year, 1, 1).weekday()
        preceeding_days = 7 - first_weekday
        if preceeding_days == 7:
            preceeding_days = 0
        if weekday == 6 and week_of_year_start == 6:
            week_of_year -= 1
        if weekday == 0 and first_weekday == 0 and week_of_year_start == 6:
            week_of_year += 1
        if week_of_year == 0:
            julian = 1 + weekday - first_weekday
        else:
            days_to_week = preceeding_days + 7 * (week_of_year - 1)
            julian = 1 + days_to_week + weekday


# 2.6 pstats.py
# Bug is handling "for" with "elif" and "and"s.
def eval_print_amount(a, b, c, d, list, msg=0):
    if a:
        for i in list:
            msg = 1
    elif b and c:
        msg = 2
    elif c and d:
        msg = 3
    return msg

assert eval_print_amount(True, False, False, False, [1]) == 1
assert eval_print_amount(True, False, False, False, []) == 0
assert eval_print_amount(False, True, True, False, []) == 2
assert eval_print_amount(False, False, True, True, []) == 3
assert eval_print_amount(False, False, False, True, []) == 0
