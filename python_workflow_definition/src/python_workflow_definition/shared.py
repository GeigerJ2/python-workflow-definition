def get_dict(**kwargs):
    # NOTE: In WG, this will automatically be wrapped in a dict with the `result` key
    return {k: v for k, v in kwargs.items()}
    # return {'dict': {k: v for k, v in kwargs.items()}}


def get_list(**kwargs):
    return list(kwargs.values())


def get_kwargs(lst):
    return {t["th"]: {"sn": t["sn"], "sh": t["sh"]} for t in lst}


def get_source_handles(edges_lst):
    source_handle_dict = {}
    for ed in edges_lst:
        if ed["sn"] not in source_handle_dict.keys():
            source_handle_dict[ed["sn"]] = [ed["sh"]]
        else:
            source_handle_dict[ed["sn"]].append(ed["sh"])
    return {
        k: list(range(len(v))) if len(v) > 1 and all([el is None for el in v]) else v
        for k, v in source_handle_dict.items()
    }