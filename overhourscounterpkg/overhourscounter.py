def progresive_hours_counter(daily_rate, amount_of_overhours):
    sum = daily_rate
    overhours = int(amount_of_overhours)
    if overhours < 3:
        sum += daily_rate * 0.15 * overhours
        print(sum)
    elif overhours < 5:
        sum += daily_rate * 0.30
        sum += daily_rate * 0.20 * (overhours - 2)
    elif overhours == 5:
        sum += daily_rate
    else:
        sum += daily_rate
        sum += daily_rate * 0.50 * (overhours - 5)
    return sum
