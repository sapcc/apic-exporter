def Unpack(data, *keys):
    """unpack ensures the value behind the keys exists
    if the value does not exists an ValueError is raised"""
    for k in keys:
        if isinstance(data, dict) and data.get(k):
            data = data[k]
        else:
            return ValueError(f"{keys} not found in data")
    return data
