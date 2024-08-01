def progresive_hours_counter(daily_rate, amount_of_overhours):
    """
    Over Hours Counter Function
    Counting Progresive overhours base on a daily rate.

    Parameters
    -----------
    daily_rate : float
        salary for one work day

    amount_of_overhours : int
        amount of overhours exact day

    Returns
    ----------
    sum : float
        exact sum of basic daily salary plus salary for over hours for that day
    """
    sum = daily_rate
    over_hours = int(amount_of_overhours)
    if over_hours < 3:
        sum += daily_rate * 0.15 * over_hours
        print(sum)
    elif over_hours < 5:
        sum += daily_rate * 0.30
        sum += daily_rate * 0.20 * (over_hours - 2)
    elif over_hours == 5:
        sum += daily_rate
    else:
        sum += daily_rate
        sum += daily_rate * 0.50 * (over_hours - 5)
    return sum
