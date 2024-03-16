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
