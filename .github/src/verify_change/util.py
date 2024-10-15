def findDiff(d1, d2, path="", changes={}):
    for k in d1:
        try:
            if k in d2:
                if type(d1[k]) is dict:
                    findDiff(d1[k], d2[k], "%s.%s" % (path, k) if path else k, changes)
                if d1[k] != d2[k] and path:
                    changes[f"{path}.{k}"] = d2[k]
                elif d1[k] != d2[k]:
                    changes[k] = d2[k]
            else:
                changes[f"{path}.{k}"] = None
        except Exception:
            changes[f"{path}.{k}"] = None
    return changes
