def binance_option_join_list(lists):
    to_return = []
    for index, data in enumerate(lists):
        if index == 0:
            to_return.append(data[:-1].replace("'", '"'))
        elif index == len(lists)-1:
            to_return.append(data[1:].replace("'", '"'))
        else:
            to_return.append(data[1:-1].replace("'", '"'))
    return ",".join(to_return)
