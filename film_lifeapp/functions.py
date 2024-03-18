# NEED A CLEAN NIP NUMBER(STR) ---------------
def nip_checker(nip):
    weight = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    try:
        lst = [int(number) for number in nip[:-1]]
    except ValueError:
        return False
    result = [weight * number for weight, number in zip(weight, lst)]
    if sum(result) % 11 == int(nip[-1]):
        return True
    return False




def progresive_hours_counter(daily_rate,amount_of_overhours):
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