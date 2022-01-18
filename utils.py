def age_meter(date1: list, date2: list) -> int:
    """
    :param date1: в формате [D, M, YYYY]
    :param date2: в формате [D, M, YYYY]
    :return: int разницу в годах
    """
    day = int(date1[0]) - int(date2[0])
    month = int(date1[1]) - int(date2[1])
    if day < 1:
        month -= 1
    year = int(date1[2]) - int(date2[2])
    if month < 1:
        year -= 1
    return int(year)
