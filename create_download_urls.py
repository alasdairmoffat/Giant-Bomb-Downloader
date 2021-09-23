import pathlib


def get_url(url, quality):
    """
    640x360 - mobile & low
    960x540 - medium
    1280x720 - alt_medium & alt_high
    1920x1080 - high & hd
    """
    qualities = {
        "mobile": "700",
        "low": "1000",
        "medium": "1800",
        "alt_medium": "2500",
        "alt_high": "3200",
        "high": "4000",
        "hd": "8000",
    }

    if quality not in qualities:
        print("invalid quality")
        return

    # split on last "."
    main_url, extension = url.rsplit(".", 1)

    return f"{main_url[:-4]}{qualities[quality]}.{extension}"


url = "https://static-giantbombvideo.cbsistatic.com/vr/2020/09/18/521732/mc_vinnyvania_09182020_4000.mp4"

print(get_url(url, "low"))
"""
qualities = {
    "mobile": 700,
    "low": 1000,
    "medium": 1800,
    "alt_medium": 2500,
    "alt_high": 3200,
    "high": 4000,
    "hd": 8000,
}

test = "hd"

print(test in qualities or test in qualities.values())

"""
